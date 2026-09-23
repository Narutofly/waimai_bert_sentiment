"""模型评估：分批前向评测、报告渲染与典型误判整理。

报告渲染与误判整理只接收普通 list/dict，不需要模型与 GPU，
由 tests/test_model_eval_report.py 覆盖；evaluate() 才需要真实模型。
"""
import hashlib
import importlib
import time
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from common.preprocess import clean_text_for_bert
from training.config import Config

TRIALS = 128
SAMPLES = 16

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


def evaluate():
    """评估模型"""
    _require_prerequisites()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    # 加载测试数据
    test_df = pd.read_csv(Config.test_raw_file, sep=',', names=['labels', 'text'])
    # 加载训练好的分词器和模型
    tokenizer = AutoTokenizer.from_pretrained(Config.model_file)
    model = AutoModelForSequenceClassification.from_pretrained(Config.model_file)
    model.to(device)
    # 开启评估模式
    model.eval()

    total_accuracy, total_duration = 0.0, 0.0
    for _ in range(TRIALS):
        samples = test_df.sample(n=SAMPLES)
        x_raw, y_test = samples['text'], samples['labels']

        start = time.perf_counter()
        # 数据预处理
        x_test = list(map(clean_text_for_bert, x_raw))
        # 分词
        inputs = tokenizer(
            text=x_test,
            return_tensors="pt",
            max_length=32,
            truncation=True,
            padding='max_length',
        )
        input_ids = inputs['input_ids'].to(device)
        attention_mask = inputs['attention_mask'].to(device)
        # 模型推理,阻断计算图
        with torch.inference_mode():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        end = time.perf_counter()

        y_pred = torch.argmax(outputs.logits,dim=-1).cpu().numpy()
        total_accuracy += accuracy_score(y_test, y_pred)
        total_duration += end - start

    print(f'Accuracy: {total_accuracy / TRIALS:.2%}')
    print(f'Duration = {total_duration / TRIALS:.3f}s')