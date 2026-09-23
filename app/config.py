"""后端基础配置，沿用原项目模型路径。"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    MODEL_PATH = str(BASE_DIR / "model" / "ft_bert_dir")
    CLASS_FILE = str(BASE_DIR / "model" / "thy_labels.txt")
    # TODO: 按团队需求补充运行配置。
