"""模型评估：分批前向评测、报告渲染与典型误判整理。

报告渲染与误判整理只接收普通 list/dict，不需要模型与 GPU，
由 tests/test_model_eval_report.py 覆盖；evaluate() 才需要真实模型。
"""
import argparse
import hashlib
import importlib
import sys
import time
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from common.preprocess import clean_text_for_bert
from training.config import Config

# README 要求全量评估测试集，不抽样、不 shuffle，故此处没有抽样次数的概念
DEFAULT_BATCH_SIZE = 64

# 与 WaimaiDataset(max_len=32) 和 app/prediction.py 的 max_length=32 对齐。
# 默认值取 32，改大只会把长文本截断点推后，与训练和线上推理的口径就不再一致。
DEFAULT_MAX_LENGTH = 32

# 类别数量，与训练时 num_labels=2 一致
EXPECTED_LABELS = 2

# 标签文件与占位名。README「已知限制」明确要求：标签文件缺失时用占位名并告警，
# **不默认推断 0=差评、1=好评** —— 万一成员 4 导出的标签顺序相反，整张指标表会
# 张冠李戴，而错标签比占位名危险得多。该文件位于 model/ 目录，不纳入 Git。
LABELS_FILE = Config.model_file.parent / 'thy_labels.txt'
LABEL_FALLBACK_NAMES = ('类别0', '类别1')

# 典型误判口径的置信度阈值。README 规定了两个口径及各自上限，
# 但未约定阈值取值，此处约定：>= HIGH 视为「模型很自信却错了」，
# <= LOW 视为「贴近决策边界」。
HIGH_CONFIDENCE = 0.90
LOW_CONFIDENCE = 0.60

# version_id 取 sha256 前若干位，长度由 README「模型版本」一节约定为 12 位
VERSION_ID_LEN = 12

REQUIRED_MODULES = ('numpy', 'pandas', 'sklearn', 'torch', 'transformers')

BUCKET_PER_CLASS = '各真实类别误判'
BUCKET_HIGH_CONFIDENCE = '高置信度误判'
BUCKET_LOW_CONFIDENCE = '低置信度误判'
BUCKET_LONGEST = '最长文本误判'
BUCKET_SHORTEST = '最短文本误判'


class EvalError(Exception):
    """评估前置条件不满足。携带稳定的 code，便于调用方分支处理。"""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f'[{code}] {message}')


def missing_dependencies():
    """检查必需依赖能否导入。全部可用返回 None，否则返回说明字符串。"""
    missing = []
    for name in REQUIRED_MODULES:
        try:
            importlib.import_module(name)
        except ImportError:
            missing.append(name)
    if not missing:
        return None
    return '缺少依赖：' + '、'.join(missing) + '，请先执行 pip install -r requirements.txt'


def fingerprint_dir(path):
    """对目录内容取指纹。

    文件名与文件内容一并纳入哈希，因此「同名文件被覆盖」也会改变 version_id
    —— 只按文件名或大小取指纹时，训练是否真的产出了新模型会判断错。
    """
    path = Path(path)
    if not path.is_dir():
        return {'available': False, 'version_id': 'unavailable'}

    digest = hashlib.sha256()
    for item in sorted(p for p in path.rglob('*') if p.is_file()):
        digest.update(item.relative_to(path).as_posix().encode('utf-8'))
        digest.update(b'\0')
        digest.update(item.read_bytes())
        digest.update(b'\0')

    return {'available': True, 'version_id': digest.hexdigest()[:VERSION_ID_LEN]}


def _display_width(text) -> int:
    """终端显示列宽：CJK 全角字符占 2 列，其余占 1 列。"""
    return sum(
        2 if unicodedata.east_asian_width(char) in ('W', 'F') else 1
        for char in str(text)
    )


def _pad(text, width: int, align: str = 'left') -> str:
    """按显示宽度而非 len() 补空格。"""
    text = str(text)
    padding = ' ' * max(0, width - _display_width(text))
    return padding + text if align == 'right' else text + padding


def _render_confusion_matrix(matrix, labels) -> str:
    """渲染混淆矩阵。首行为标题，其后依次是表头、各类别行与合计行，各行等宽。"""
    title = '混淆矩阵'
    size = len(labels)
    if not size or not matrix:
        return f'{title}\n无类别'

    row_totals = [sum(row) for row in matrix]
    col_totals = [sum(matrix[r][c] for r in range(size)) for c in range(size)]
    grand_total = sum(row_totals)

    head_width = max(_display_width(text) for text in (*labels, '真实\\预测', '合计'))
    # 表头行每列放的是预测类别名，列宽需同时容纳类别名与计数
    cell_widths = [
        max([_display_width(labels[c]), _display_width(col_totals[c])]
            + [_display_width(matrix[r][c]) for r in range(size)])
        for c in range(size)
    ]
    total_width = max([_display_width(grand_total)]
                      + [_display_width(value) for value in row_totals])

    def build(head, cells, tail) -> str:
        columns = [_pad(head, head_width, 'right')]
        columns += [_pad(cell, width, 'right') for cell, width in zip(cells, cell_widths)]
        columns.append(_pad(tail, total_width, 'right'))
        return '  '.join(columns)

    lines = [title, build('真实\\预测', list(labels), '合计')]
    for index, label in enumerate(labels):
        lines.append(build(label, list(matrix[index]), row_totals[index]))
    lines.append(build('合计', col_totals, grand_total))
    return '\n'.join(lines)


def _render_metrics_table(metrics) -> str:
    """渲染各类别指标表，含宏平均与加权平均汇总行。各行等宽。"""
    per_class = metrics.get('per_class') or []
    headers = ('类别', '支持数', 'Precision', 'Recall', 'F1')

    def number(value) -> str:
        return '-' if value is None else f'{float(value):.4f}'

    rows = []
    for item in per_class:
        rows.append([
            str(item.get('label') or f"类别{item.get('label_id', '-')}"),
            str(item.get('support', '-')),
            number(item.get('precision')),
            number(item.get('recall')),
            number(item.get('f1')),
        ])

    # README 只约定汇总宏平均 F1 与加权 F1，其余汇总列留空
    rows.append(['宏平均', '-', '-', '-', number(metrics.get('macro_f1'))])
    rows.append(['加权平均', '-', '-', '-', number(metrics.get('weighted_f1'))])

    widths = [
        max(_display_width(headers[i]), *(_display_width(row[i]) for row in rows))
        for i in range(len(headers))
    ]

    lines = []
    for row in [list(headers)] + rows:
        # 末列右对齐，保证每行右侧不留填充，rstrip 后各行宽度仍一致
        cells = [
            _pad(row[i], widths[i], 'left' if i == 0 else 'right')
            for i in range(len(row))
        ]
        lines.append('  '.join(cells))
    return '\n'.join(lines)


def _to_py(value):
    """把 numpy 标量转成 Python 原生类型，使其可被 json 序列化。"""
    if isinstance(value, np.generic):
        return value.item()
    return value


def _mine_misclassifications(frame, y_true, y_pred, probabilities,
                             label_names, token_lengths, reached_max_length):
    """整理全部误判，并标注每条命中的典型误判口径。

    line_number 为 CSV 行号，即 frame 索引 + 1，供复核时回 test.csv 核对原文。

    这里返回**全部**误判，不做上限裁剪 —— README 的「每类 5 条 / 高置信度 10 条」
    等上限属于报告选取阶段，两者是「全部误判明细」与「挑出的典型样本」两个产物。
    """
    records = []
    has_text = 'text' in frame.columns

    for position in range(len(frame)):
        true_id, pred_id = int(y_true[position]), int(y_pred[position])
        if true_id == pred_id:
            continue

        # 置信度取「被判成的那个类别」的概率，即模型对这次错误判断的自信程度
        confidence = float(probabilities[position][pred_id])
        buckets = [BUCKET_PER_CLASS]
        if confidence >= HIGH_CONFIDENCE:
            buckets.append(BUCKET_HIGH_CONFIDENCE)
        elif confidence <= LOW_CONFIDENCE:
            buckets.append(BUCKET_LOW_CONFIDENCE)

        records.append({
            'line_number': int(frame.index[position]) + 1,
            'text': frame['text'].iloc[position] if has_text else '',
            'true_label_id': true_id,
            'true_label': label_names[true_id],
            'pred_label_id': pred_id,
            'pred_label': label_names[pred_id],
            'confidence': confidence,
            'token_length': int(token_lengths[position]),
            'reached_max_length': bool(reached_max_length[position]),
            'buckets': buckets,
        })

    # 最长 / 最短口径依赖全体误判的比较，故在收集完成后统一标注
    if records:
        lengths = [record['token_length'] for record in records]
        longest, shortest = max(lengths), min(lengths)
        for record in records:
            if record['token_length'] == longest:
                record['buckets'].append(BUCKET_LONGEST)
            if record['token_length'] == shortest:
                record['buckets'].append(BUCKET_SHORTEST)

    records.sort(key=lambda record: record['confidence'], reverse=True)
    return records


def _require_prerequisites():
    """评估前置条件检查。不满足时抛 EvalError，避免产出与后端口径不一致的报告。"""
    missing = missing_dependencies()
    if missing:
        raise EvalError('DEPENDENCY_MISSING', missing)
    if not Config.model_file.is_dir():
        raise EvalError('MODEL_DIR_MISSING', f'未找到微调模型目录：{Config.model_file}')


def load_label_names() -> tuple:
    """读取类别标签，缺失或数量不符时退回占位名并告警。

    不猜「0=差评、1=好评」：占位名只是不好看，猜错标签会让整张指标表失去意义。
    """
    if not LABELS_FILE.is_file():
        print(f'警告：未找到标签文件 {LABELS_FILE}，本次使用占位名 '
              f'{"、".join(LABEL_FALLBACK_NAMES)}；标签含义请以成员 4 导出的标签文件为准')
        return LABEL_FALLBACK_NAMES

    names = tuple(
        line.strip()
        for line in LABELS_FILE.read_text(encoding='utf-8').splitlines()
        if line.strip()
    )
    if len(names) != EXPECTED_LABELS:
        print(f'警告：{LABELS_FILE} 有 {len(names)} 个标签，期望 {EXPECTED_LABELS} 个，'
              f'本次使用占位名 {"、".join(LABEL_FALLBACK_NAMES)}')
        return LABEL_FALLBACK_NAMES
    return names


def _build_metrics(y_true, y_pred, label_names) -> dict:
    """按 README 口径计算各类别指标，以及宏平均 F1 与加权 F1。"""
    label_ids = list(range(len(label_names)))
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=label_ids, zero_division=0,
    )
    return {
        'per_class': [
            {
                'label_id': label_id,
                'label': label_names[label_id],
                'support': _to_py(support[label_id]),
                'precision': float(precision[label_id]),
                'recall': float(recall[label_id]),
                'f1': float(f1[label_id]),
            }
            for label_id in label_ids
        ],
        # README 只约定汇总宏平均 F1 与加权 F1，其余汇总列由渲染层留空
        'macro_f1': float(f1_score(y_true, y_pred, average='macro', zero_division=0)),
        'weighted_f1': float(
            f1_score(y_true, y_pred, average='weighted', zero_division=0)
        ),
    }


def evaluate(batch_size: int = DEFAULT_BATCH_SIZE,
             max_length: int = DEFAULT_MAX_LENGTH) -> dict:
    """全量评估测试集，打印指标表并返回评估摘要。

    口径由 README「评估口径」一节约定：按 test.csv 原始顺序全量前向，
    不抽样、不 shuffle。早期版本的「随机抽 16 条 × 128 次」已整体替换。
    """
    _require_prerequisites()
    label_names = load_label_names()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # header=None：test.csv 没有表头。不指定的话 pandas 会把第一条真实样本
    # 当成列名，既少评一条，又让误判的 line_number 整体错位一行。
    test_df = pd.read_csv(
        Config.test_raw_file, sep=',', names=['labels', 'text'], header=None,
    )

    tokenizer = AutoTokenizer.from_pretrained(Config.model_file)
    model = AutoModelForSequenceClassification.from_pretrained(Config.model_file)
    model.to(device)
    model.eval()

    x_test = list(map(clean_text_for_bert, test_df['text']))
    y_true = test_df['labels'].to_numpy()

    prediction_batches, probability_batches, length_batches = [], [], []
    start = time.perf_counter()
    for offset in range(0, len(x_test), batch_size):
        inputs = tokenizer(
            text=x_test[offset:offset + batch_size],
            return_tensors='pt',
            max_length=max_length,
            truncation=True,
            padding='max_length',
        )
        input_ids = inputs['input_ids'].to(device)
        attention_mask = inputs['attention_mask'].to(device)
        # 模型推理,阻断计算图
        with torch.inference_mode():
            logits = model(input_ids=input_ids, attention_mask=attention_mask).logits
        probabilities = torch.softmax(logits, dim=-1).cpu().numpy()
        prediction_batches.append(probabilities.argmax(axis=-1))
        probability_batches.append(probabilities)
        # attention_mask 中 1 的个数即真实 token 数，用于最长 / 最短文本误判口径
        length_batches.append(attention_mask.sum(dim=1).cpu().numpy())
    duration = time.perf_counter() - start

    y_pred = np.concatenate(prediction_batches)
    probabilities = np.concatenate(probability_batches)
    token_lengths = np.concatenate(length_batches)

    matrix = [[0] * len(label_names) for _ in label_names]
    for true_id, pred_id in zip(y_true, y_pred):
        matrix[int(true_id)][int(pred_id)] += 1

    metrics = _build_metrics(y_true, y_pred, label_names)
    misclassifications = _mine_misclassifications(
        test_df, y_true, y_pred, probabilities,
        label_names, token_lengths, token_lengths >= max_length,
    )

    print(f'评估样本 {len(y_true)} 条（全量，按 test.csv 原始顺序，未抽样）')
    print(f'批大小 {batch_size}，最大长度 {max_length}，前向耗时 {duration:.2f}s')
    print()
    print(_render_confusion_matrix(matrix, label_names))
    print()
    print(_render_metrics_table(metrics))
    print()
    print(f'误判 {len(misclassifications)} 条；明细整理逻辑已就绪，'
          '报告落盘（report.md / metrics.json）尚未实现')

    return {
        'total': int(len(y_true)),
        'accuracy': float(accuracy_score(y_true, y_pred)),
        'macro_f1': metrics['macro_f1'],
        'weighted_f1': metrics['weighted_f1'],
        'per_class': metrics['per_class'],
        'confusion_matrix': matrix,
        'misclassifications': misclassifications,
        'batch_size': batch_size,
        'max_length': max_length,
        'duration_seconds': round(duration, 3),
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description='全量评估已交付的微调模型（等价于 run_pipeline.py --eval-only）',
    )
    parser.add_argument(
        '--batch-size', type=int, default=DEFAULT_BATCH_SIZE,
        help=f'评估批大小（默认 {DEFAULT_BATCH_SIZE}）',
    )
    parser.add_argument(
        '--max-length', type=int, default=DEFAULT_MAX_LENGTH,
        help=f'最大序列长度（默认 {DEFAULT_MAX_LENGTH}，与训练和在线推理一致）',
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    """独立评估入口。退出码与 run_pipeline.py 一致：0 完成 / 1 失败 / 3 跳过。"""
    args = parse_args(argv)
    try:
        evaluate(batch_size=args.batch_size, max_length=args.max_length)
    except EvalError as error:
        print(f'跳过：{error}')
        return 3
    except Exception as error:  # noqa: BLE001 —— 兜底归类为真实失败
        print(f'失败：{type(error).__name__}: {error}')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
    print(f'Duration = {total_duration / TRIALS:.3f}s')