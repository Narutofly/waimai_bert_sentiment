# 外卖评价情感分析 · 初始化版本

参照 `E:/project/waimai-bert-sentiment`，保留原项目目录与文件组织，
清除前端、后端推理和模型训练、验证、评估的业务实现，只保留基础入口和 TODO，供团队开发。
原项目误拼的 `traning` 更正为 `training`。不包含真实数据、模型权重或原项目 Git 历史。

## 原项目结构

```text
.
├── app/                     # 后端 Flask
│   ├── __init__.py          # 应用工厂
│   ├── config.py            # 后端配置
│   ├── extensions.py        # 模型加载与推理 TODO
│   └── prediction.py        # API 路由 TODO
├── common/                  # 共享文本预处理 TODO
├── data/
│   ├── raw/                 # 训练、验证、测试数据
│   └── pre/                 # 预处理数据
├── frontend/                # Vue 3 + Vite 前端
│   └── src/
│       ├── components/      # InputPanel、ResultsPanel、AppIcon 占位
│       ├── composables/     # useAnalysis 状态管理 TODO
│       ├── App.vue          # 页面入口
│       ├── api.js           # 接口请求 TODO
│       ├── main.js          # Vue 启动入口
│       └── style.css        # 基础样式
├── model/                   # 本地模型及标签，不提交实际文件
├── output/                  # 运行产物，不提交实际文件
├── training/                 # 模型训练与验证（修正原目录拼写）
│   ├── __init__.py
│   ├── config.py            # 数据和模型路径
│   ├── dataset.py           # 数据读取与编码 TODO
│   ├── model_train.py       # 训练及验证 TODO
│   └── model_eval.py        # 测试集评估 TODO
├── requirements.txt         # 最小后端依赖
├── run_pipeline.py          # 离线入口
└── wsgi.py                  # 后端入口
```

## 启动

后端不需要下载模型即可启动。项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe wsgi.py
```

健康检查：`http://127.0.0.1:8000/api/v1/`。
前端建议 Node.js 22.12+，另开终端执行：

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

访问 `http://127.0.0.1:5173`，当前只有初始化占位页面。
在根目录执行 `python run_pipeline.py` 只显示 TODO 提示，不启动训练。
模型开发需要的 PyTorch、Transformers 等依赖由负责人按环境补充到 requirements.txt。

## 团队开发约定

前端负责 `frontend/`，后端负责 `app/`，模型负责人负责 `training/`。
共同维护 `common/preprocess.py`，保证训练、验证、评估与推理使用相同清洗规则。
训练期间使用验证集选择模型，最终在独立测试集上评估。
沿用模型路径 `model/google-bert/bert-base-chinese`、`model/ft_bert_dir`，
标签文件为 `model/thy_labels.txt`，行序必须与模型类别编号一致。
所有文本文件使用 UTF-8，真实数据、权重、依赖目录与本地环境配置不提交 Git。

| 接口 | 用途 | 当前状态 |
| --- | --- | --- |
| GET `/api/v1/` | 健康检查 | HTTP 200 |
| GET `/api/v1/labels` | 标签列表 | HTTP 501，待实现 |
| POST `/api/v1/classify` | JSON 中 text 字符串或字符串数组 | HTTP 501，待实现 |
| POST `/api/v1/classify_from_file` | text_file 字段上传 UTF-8 TXT | HTTP 501，待实现 |

推理成功响应沿用原项目的 `code`、`results`；每条结果包含
`text`、`label`、`confidence`（百分比字符串）、`is_certain`。当前不产生任何预测结果。

## Gitee

`origin` 关联 [waimai_bert_sentiment](https://gitee.com/whoamber/waimai_bert_sentiment)，
本地分支为 `main`。本次仅初始化和关联，不自动推送。
有仓库权限的团队成员可执行 `git push -u origin main` 首次上传。
