"""离线训练流水线入口。

三步串行：数据准备 → 训练 → 评估。每一步都必须先验证产物真的落盘，才算完成，
绝不出现「没做完却报告成功」。

退出码（与 README「快速开始」一节一致）：
    0  三步全部真的完成
    1  有步骤真实失败（异常或产物缺失）
    3  没有失败，但有步骤因「尚未实现」或「依赖缺失」被跳过

「产物缺失」与「依赖缺失」的区分口径：
    产物缺失 —— 本步骤自己应当写出的东西没写出来，判为失败（退出码 1）。
    依赖缺失 —— 本步骤依赖的外部输入（基座模型、已交付的微调模型、第三方库）不在，
                判为跳过（退出码 3）。跳过不等于成功。
"""
import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.preprocess import clean_text_for_bert
from training.config import Config

EXIT_DONE = 0
EXIT_FAILED = 1
EXIT_SKIPPED = 3

DONE = 'done'
SKIPPED = 'skipped'
FAILED = 'failed'

STATUS_LABEL = {DONE: '完成', SKIPPED: '跳过', FAILED: '失败'}

# 模型导出后必须存在的文件。权重二选一，fast 分词器只需 tokenizer.json
REQUIRED_MODEL_FILES = ('config.json', 'tokenizer_config.json', 'tokenizer.json')
MODEL_WEIGHT_FILES = ('model.safetensors', 'pytorch_model.bin')


class DependencyMissing(RuntimeError):
    """外部依赖缺失。该步跳过，而不是判为失败。"""


@dataclass
class StepResult:
    """一步的执行结论。"""

    name: str
    status: str
    detail: str = ''


def _require_file(path: Path, what: str) -> None:
    """文件必须存在且非空，否则算产物缺失（真实失败）。"""
    if not path.is_file():
        raise FileNotFoundError(f'{what}缺失：{path}')
    if path.stat().st_size == 0:
        raise ValueError(f'{what}是空文件：{path}')


def _read_raw_corpus(raw_file: Path) -> tuple:
    """读取 `标签,文本` 形式的原始语料，返回 (记录列表, 丢弃行数)。

    原始 CSV 的文本字段带引号且自身可能含逗号，故按 CSV 规则解析而不是手工切分，
    否则文本里的逗号会被误当成字段边界。解析后统一清洗：
    clean_text_for_bert 会保留 \\n 与 \\t，而预处理产物是一行一条记录，
    因此再把所有空白折叠成单个空格，保证行结构与 load_corpus 的读取方式兼容。
    """
    records = []
    discarded = 0
    with open(raw_file, encoding='utf-8', newline='') as file_obj:
        for row in csv.reader(file_obj):
            if len(row) < 2:
                discarded += 1
                continue
            text = ' '.join(clean_text_for_bert(row[1]).split())
            if not text:
                discarded += 1
                continue
            records.append((row[0].strip(), text))
    return records, discarded


def prepare_data() -> str:
    """数据准备：清洗 data/raw 下的原始语料，写出 data/pre 下的训练与验证语料。

    产物格式与 load_corpus 的读取方式一致（每行 `标签,文本`），可直接被其读取。
    需要说明的是：当前 training/model_train.py 仍直接读 data/raw/*.csv
    （load_corpus 内部已调用 clean_text_for_bert），因此本步骤的产物暂时还没有
    下游消费者，是给后续训练切换到「读预处理产物」准备的。
    """
    jobs = (
        ('训练', Config.train_raw_file, Config.train_pre_file),
        ('验证', Config.valid_raw_file, Config.valid_pre_file),
    )
    summary = []
    for label, raw_file, pre_file in jobs:
        _require_file(raw_file, f'{label}集原始数据')
        records, discarded = _read_raw_corpus(raw_file)
        if not records:
            raise ValueError(f'{label}集清洗后没有任何可用语料：{raw_file}')

        pre_file.parent.mkdir(parents=True, exist_ok=True)
        pre_file.write_text(
            ''.join(f'{tag},{text}\n' for tag, text in records),
            encoding='utf-8',
        )

        # 产物校验：行数必须与读入的记录数一致，否则说明写坏了
        written = sum(1 for _ in pre_file.open(encoding='utf-8'))
        if written != len(records):
            raise RuntimeError(
                f'{label}集预处理产物行数不符：写入 {written} 行，应为 {len(records)} 行'
            )

        detail = f'{label}集 {len(records)} 条 → {pre_file.name}'
        if discarded:
            detail += f'（丢弃 {discarded} 行空文本或格式不符的记录）'
        summary.append(detail)
    return '；'.join(summary)


def run_train() -> str:
    """训练并导出模型。基座模型不在属「依赖缺失」，如实跳过而不是伪装成功。"""
    if not Config.bert_model_dir.is_dir():
        raise DependencyMissing(
            f'基座模型目录不存在：{Config.bert_model_dir}，'
            '请先把 bert-base-chinese 放到位再重跑训练'
        )

    from training.model_train import train

    train()

    # 训练报告成功之后才校验产物，防止「跑完了但没存下来」
    model_dir = Config.model_file
    if not model_dir.is_dir():
        raise FileNotFoundError(f'模型目录未生成：{model_dir}')
    for name in REQUIRED_MODEL_FILES:
        _require_file(model_dir / name, '模型文件')
    if not any((model_dir / name).is_file() for name in MODEL_WEIGHT_FILES):
        raise FileNotFoundError(
            f'模型权重缺失：{model_dir} 下没有 {" 或 ".join(MODEL_WEIGHT_FILES)}'
        )
    return f'模型已导出到 {model_dir}'


def run_eval(batch_size: int, max_length: int) -> str:
    """全量评估测试集。模型或依赖缺失属「依赖缺失」，如实跳过。"""
    from training.model_eval import EvalError, evaluate

    try:
        summary = evaluate(batch_size=batch_size, max_length=max_length)
    except EvalError as error:
        # EvalError 只在依赖或前置产物不满足时抛出，属可跳过的情形
        raise DependencyMissing(error.message) from error
    return (
        f'全量 {summary["total"]} 条，准确率 {summary["accuracy"]:.2%}，'
        f'宏平均 F1 {summary["macro_f1"]:.4f}，'
        f'误判 {len(summary["misclassifications"])} 条'
    )


def build_plan(args) -> list:
    """按参数决定每一步是「执行」还是「跳过」。--eval-only 优先于 --skip-prep。"""
    evaluate_step = ('评估', lambda: run_eval(args.batch_size, args.max_length), '')
    if args.eval_only:
        reason = '--eval-only：只评估已交付的模型'
        return [
            ('数据准备', None, reason),
            ('训练', None, reason),
            evaluate_step,
        ]
    if args.skip_prep:
        return [
            ('数据准备', None, '--skip-prep：复用已有预处理结果'),
            ('训练', run_train, ''),
            evaluate_step,
        ]
    return [
        ('数据准备', prepare_data, ''),
        ('训练', run_train, ''),
        evaluate_step,
    ]


def run_step(index: int, total: int, name: str, action, skip_reason: str) -> StepResult:
    """执行一步并归类其结论。"""
    print(f'\n=== [Step {index}/{total}] {name} ===')
    if action is None:
        print(f'跳过：{skip_reason}')
        return StepResult(name, SKIPPED, skip_reason)

    try:
        detail = action()
    except DependencyMissing as error:
        print(f'跳过：{error}')
        return StepResult(name, SKIPPED, str(error))
    except Exception as error:  # noqa: BLE001 —— 兜底归类为真实失败
        print(f'失败：{type(error).__name__}: {error}')
        return StepResult(name, FAILED, f'{type(error).__name__}: {error}')

    print(f'完成：{detail}')
    return StepResult(name, DONE, detail)


def summarize(results: list) -> int:
    """打印结论并返回退出码。被跳过的步骤不会返回 0。"""
    print('\n=== 流水线结论 ===')
    for result in results:
        print(f'  {result.name}：{STATUS_LABEL[result.status]}  {result.detail}')

    if any(result.status == FAILED for result in results):
        code, verdict = EXIT_FAILED, '存在真实失败，未完成的步骤不算成功'
    elif any(result.status == SKIPPED for result in results):
        code, verdict = EXIT_SKIPPED, '没有失败，但有步骤被跳过，不能视为全部完成'
    else:
        code, verdict = EXIT_DONE, '三步全部真的完成'
    print(f'退出码 {code}：{verdict}')
    return code


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description='离线训练流水线：数据准备 → 训练 → 评估',
    )
    parser.add_argument(
        '--eval-only', action='store_true',
        help='只评估已交付的模型，跳过数据准备与训练',
    )
    parser.add_argument(
        '--skip-prep', action='store_true',
        help='复用已有预处理结果，只重跑训练与评估',
    )
    parser.add_argument(
        '--batch-size', type=int, default=64,
        help='评估批大小（默认 64）',
    )
    parser.add_argument(
        '--max-length', type=int, default=32,
        help='评估最大序列长度（默认 32，与训练和在线推理保持一致）',
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    """离线训练流水线程序入口。"""
    args = parse_args(argv)
    plan = build_plan(args)
    results = [
        run_step(index, len(plan), name, action, skip_reason)
        for index, (name, action, skip_reason) in enumerate(plan, start=1)
    ]
    return summarize(results)


if __name__ == '__main__':
    sys.exit(main())
