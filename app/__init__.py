"""Flask 应用工厂；初始化时不加载模型。"""

from flask import Flask

from app.config import Config
from app.prediction import api_v1_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    app.json.ensure_ascii = False
    app.register_blueprint(api_v1_bp)
    # TODO(backend): 注册日志、统一异常处理和推理服务。
    return app
