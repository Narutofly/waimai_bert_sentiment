import sys
from pathlib import Path

from training.model_eval import evaluate
from training.model_train import train

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))


def main():
    """离线训练流水线程序入口"""
    print("\n=== [Step 1/2] 开始训练和导出文本分类模型 ===")
    # Todo: 执行模型训练和导出
    # train()
    print("\n=== [Step 2/2] 启动服务之前对模型进行评估 ===")
    # Todo: 执行模型推理和评估
    evaluate()

if __name__ == "__main__":
    main()