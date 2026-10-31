import time

import pandas as pd
import torch
from sklearn.metrics import accuracy_score
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from common.preprocess import clean_text_for_bert
from training.config import Config

TRIALS = 128
SAMPLES = 16

def evaluate():
    """评估模型"""
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

        # 计时只覆盖模型推理,不含数据预处理、分词和张量搬运
        # CUDA 是异步执行,不先同步的话计时会在核函数算完之前就结束
        if device.type == 'cuda':
            torch.cuda.synchronize()
        start = time.perf_counter()
        # 模型推理,阻断计算图
        with torch.inference_mode():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        if device.type == 'cuda':
            torch.cuda.synchronize()
        end = time.perf_counter()

        y_pred = torch.argmax(outputs.logits,dim=-1).cpu().numpy()
        total_accuracy += accuracy_score(y_test, y_pred)
        total_duration += end - start

    print(f'测试集样本数：{len(test_df)}，抽样 {TRIALS} 轮 × 每轮 {SAMPLES} 条')
    print(f'平均准确率：{total_accuracy / TRIALS:.2%}')
    print(f'单次平均推理耗时：{total_duration / TRIALS:.3f}s')