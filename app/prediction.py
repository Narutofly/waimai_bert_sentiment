"""保留原项目接口路径，业务逻辑待实现。"""

from flask import Blueprint

api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")


@api_v1_bp.get("/")
def home():
    return {"code": 200, "message": "API v1", "status": "scaffold"}


def not_implemented(feature):
    return {"code": 501, "message": f"{feature}尚未实现", "results": []}, 501


@api_v1_bp.get("/labels")
def labels():
    # TODO: 读取 model/thy_labels.txt，返回标签列表。
    return not_implemented("标签接口")


@api_v1_bp.post("/classify")
def classify():
    # TODO: 校验 text 字段，执行文本推理并返回分类结果。
    return not_implemented("文本推理")


@api_v1_bp.post("/classify_from_file")
def classify_from_file():
    # TODO: 读取 text_file 上传字段，按 UTF-8 逐行处理并推理。
    return not_implemented("文件推理")
