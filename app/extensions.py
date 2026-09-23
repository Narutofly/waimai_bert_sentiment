"""模型生命周期与推理服务接口预留。"""


class TextClassifier:
    def load(self, model_path):
        # TODO(backend, ml): 加载分词器和模型，选择设备并切换 eval 模式。
        raise NotImplementedError("模型加载尚未实现")

    def predict(self, texts):
        # TODO(backend, ml): 复用共享预处理，批量推理并映射标签。
        raise NotImplementedError("模型推理尚未实现")
