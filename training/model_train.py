"""
模型训练
"""
import time
import torch
from torch import optim
from torch.nn import CrossEntropyLoss
from torch.utils.data import DataLoader
from transformers import  AutoTokenizer, AutoModelForSequenceClassification
from training.config import Config
from training.dataset import WaimaiDataset, load_corpus

def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 加载训练集和验证集语料
    corpus = load_corpus(Config.train_raw_file)
    valid_corpus = load_corpus(Config.valid_raw_file)
    if not valid_corpus:
        raise ValueError("验证集为空，无法计算准确率")

    # 加载分词器和外卖数据集
    tokenizer = AutoTokenizer.from_pretrained(Config.bert_model_dir)
    dataset = WaimaiDataset(corpus, tokenizer)
    valid_dataset = WaimaiDataset(valid_corpus, tokenizer)

    # 创建dataloader
    dataloader = DataLoader(
        dataset=dataset,
        batch_size=256,
        shuffle=True,
        num_workers=4,
        drop_last=True,
        persistent_workers=True,
    )

    valid_dataloader = DataLoader(
        dataset=valid_dataset,
        batch_size=256,
        shuffle=False,
        drop_last=False,
    )

    # 创建模型
    model = AutoModelForSequenceClassification.from_pretrained(
        Config.bert_model_dir,
        num_labels=2,
    )

    # 冻结embedding参数
    for parameter in model.bert.embeddings.parameters():
        parameter.requires_grad = False

    # 冻结前3层参数
    for layer in model.bert.encoder.layer[:3]:
        for parameter in layer.parameters():
            parameter.requires_grad = False

    # 模型进设备
    model.to(device)

    loss_fn = CrossEntropyLoss()
    optimizer = optim.AdamW([
        {'params': model.bert.encoder.layer[3:].parameters(), 'lr': 1e-5},
        {'params': model.classifier.parameters(), 'lr': 2e-4},
    ])

    for epoch in range(10):
        start = time.perf_counter()
        model.train()

        total_loss = 0.0
        for batch in dataloader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            label = batch['label'].to(device)
            # 梯度清零
            optimizer.zero_grad()
            # 正向传播
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
            )
            # 计算损失
            loss = loss_fn(outputs.logits, label)
            # 反向传播
            loss.backward()
            # 参数更新
            optimizer.step()
            total_loss += loss.item()

        # 每轮训练后验证；关闭 dropout 和梯度计算，不更新模型参数
        model.eval()
        correct = 0
        total = 0

        with torch.no_grad():
            for batch in valid_dataloader:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                label = batch['label'].to(device)
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                )
                predictions = outputs.logits.argmax(dim=1)
                correct += (predictions == label).sum().item()
                total += label.size(0)
        valid_accuracy = correct / total
        end = time.perf_counter()
        print(f'Epoch:{epoch+1}, Loss:{total_loss/len(dataloader):.3f}, '
              f'Valid Accuracy:{valid_accuracy:.2%}, time:{end-start:.3f}s')

    # 保存模型
    tokenizer.save_pretrained(Config.model_file)
    model.save_pretrained(Config.model_file)
