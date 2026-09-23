# 外卖评价情感分析

基于中文 BERT 的外卖评价二分类项目，目标是将评价识别为「差评」或「好评」，并通过后端接口和前端页面展示分析结果。

项目仓库：[Gitee / waimai_bert_sentiment](https://gitee.com/whoamber/waimai_bert_sentiment)。

项目已进入前后端联调阶段：后端可加载微调模型提供推理接口，前端页面可调用真实接口展示结果。以下分工基于现有目录，不额外拆分项目架构；成员 1～5 可替换为实际姓名。

## 当前进度

已完成：

- `data/raw/` 下三个 CSV 就绪，共 11,969 条：训练集 9,575、验证集 1,197、测试集 1,197；标签为差评 `0` / 好评 `1`，比例约 2:1，无缺失文本，各集合内部无重复样本。
- `common/preprocess.py` 提供训练与推理共用的清洗函数 `clean_text_for_bert`（HTML 标签、Emoji、控制字符清理与 Unicode 归一化）。
- `training/dataset.py` 完成语料读取与分词编码；`training/model_train.py` 完成 BERT 微调（冻结 embedding 与前 3 层），逐轮打印验证集准确率，并把模型与分词器导出到 `model/ft_bert_dir/`。
- `app/` 提供 Flask 应用工厂与 4 个推理接口，模型与分词器延迟加载并在进程内复用；启动入口为 `wsgi.py`。
- `frontend/` 为 Vue 3 + Vite 页面，支持文本输入与 TXT 导入、批量分析、筛选排序、置信度分布和 CSV 导出。
- 前后端已联通：页面可调用真实模型并展示标签与置信度。

尚未完成：

- `training/model_eval.py` 的 `evaluate()` 仍为空函数，尚无测试集准确率、Precision/Recall/F1 和混淆矩阵。
- `run_pipeline.py` 第 2 步的评估尚未接入。
- `requirements.txt` 未列出 PyTorch、Transformers、jieba（见「环境与运行说明」）。
- 前端模型报告页期望的 `GET /api/v1/model-info` 尚未实现，页面该区域显示「待接入」。
- 前端「导入 TXT」在浏览器本地读取后调用 `/api/v1/classify`，后端 `classify_from_file` 接口暂无调用方。

## 项目结构

```text
.
├── app/                         # 后端：应用工厂、配置、扩展与推理接口
│   ├── __init__.py              # create_app 工厂、CORS 与全局异常处理
│   ├── config.py                # 分环境配置、模型与标签文件路径
│   ├── extensions.py            # 分类器单例扩展，模型/分词器/标签延迟加载
│   └── prediction.py            # /api/v1 蓝图与预测接口
├── common/                      # 训练与推理共用的预处理
│   ├── __init__.py
│   └── preprocess.py            # clean_text_for_bert 文本清洗
├── data/
│   └── raw/                     # UTF-8、无表头，每行 标签,"评价文本"
│       ├── train.csv            # 训练集 9,575 条
│       ├── valid.csv            # 验证集 1,197 条
│       └── test.csv             # 测试集 1,197 条
├── frontend/                    # 前端：Vue 3 + Vite
│   ├── src/
│   │   ├── App.vue              # 页面框架、状态汇总与接口调用
│   │   ├── main.js
│   │   ├── style.css
│   │   ├── components/          # AnalyzerCard、ReviewFeed、TopicPanel、ModelReport、InsightPanel、AppIcon
│   │   └── services/
│   │       └── sentiment.js     # 接口封装与演示模式（mock）开关
│   ├── .env.example             # 接口地址与 mock 开关示例
│   ├── index.html
│   ├── package.json
│   └── vite.config.js           # 5173 端口与 /api 代理
├── model/                       # 本地模型资源，不纳入 Git
│   ├── google-bert/
│   │   └── bert-base-chinese/   # 预训练模型与分词器
│   ├── ft_bert_dir/             # 微调导出的模型与分词器（约 400MB）
│   └── thy_labels.txt           # 类别编号与中文标签映射
├── training/
│   ├── __init__.py
│   ├── config.py                # 数据与模型路径配置
│   ├── dataset.py               # 语料读取、清洗与分词编码
│   ├── model_train.py           # 模型训练及训练期间验证
│   └── model_eval.py            # 独立测试集评估（待实现）
├── requirements.txt             # Python 依赖（待补齐 PyTorch、Transformers、jieba）
├── run_pipeline.py              # 离线流程入口
├── wsgi.py                      # 后端启动入口
└── README.md
```

`data/pre/` 与 `model/ft_bert_dir/` 已在 `training/config.py` 中预留。目前 `model/ft_bert_dir/` 已存放微调导出的模型与分词器；`data/pre/` 目录尚不存在，其中配置的 `tmf_train.txt`、`tmf_valid.txt` 也还没有任何代码读取。

## 五人分工

以下是立项时的任务划分，用于说明各成员的负责范围；各部分的完成情况见上方「当前进度」。

| 成员 | 岗位 | 主要负责范围 | 核心交付物 |
| --- | --- | --- | --- |
| 成员 1 | 前端开发 | `frontend/` | Vue 3 页面、文本与文件输入、结果展示、接口联调 |
| 成员 2 | 后端开发 | `app/` | Flask 应用、模型加载、推理接口、参数校验与错误处理 |
| 成员 3 | 数据处理 | `common/`、`training/dataset.py`、`data/` | 数据检查、共享清洗函数、训练与评估使用的数据集 |
| 成员 4 | 模型训练 | `training/model_train.py`、`training/config.py` | BERT 微调、每轮验证、最佳模型及分词器导出 |
| 成员 5 | 模型评估与集成 | `training/model_eval.py`、`run_pipeline.py`、`README.md` | 测试集评估报告、完整离线流程、联调与验收记录 |

### 成员 1：前端开发

- 在 `frontend/` 内初始化 Vue 3 + Vite 工程，补充依赖清单与启动命令。
- 实现单条/多条评价输入、UTF-8 TXT 文件上传与结果展示。
- 展示原始文本、预测标签、置信度；处理加载中、空结果、请求失败等状态。
- 按下方接口约定与成员 2 联调；筛选和 CSV 导出可在基本流程完成后补充。

**验收标准：** 页面可独立启动，文本和文件两条流程均可调用真实接口，错误信息清楚可见。

### 成员 2：后端开发

- 在 `app/` 内实现 Flask 应用工厂、配置、路由和推理服务，补充实际启动入口与命令。
- 加载成员 4 交付的模型和分词器，复用已加载对象，正确设置设备及推理模式。
- 复用成员 3 提供的文本清洗函数，按模型约定编码输入并输出标签和置信度。
- 实现文本、文件类型与编码校验，统一错误响应，并与成员 1 确定批量条数和上传大小限制。

**验收标准：** 约定接口可调用；异常输入有明确响应；接口预测与离线推理在同一输入和配置下保持一致。

### 成员 3：数据处理

- 检查三个 CSV 的格式、缺失值、重复样本、标签范围和类别分布，记录各集合样本数。
- 检查训练集、验证集和测试集之间的重复样本，防止数据泄漏；调整已有划分时记录原因和版本。
- 在 `common/` 内实现统一清洗函数，在 `training/dataset.py` 中实现 CSV 读取、分词编码和数据集封装。
- 与成员 4 约定批次字段、最大长度、截断与填充方式；向成员 2 提供相同的清洗规则。

**验收标准：** 数据可稳定读取与编码；标签和文本正确对应；数据统计、划分规则及清洗边界样例可复核。

### 成员 4：模型训练

- 在 `training/config.py` 中集中维护路径、随机种子、学习率、批大小、训练轮数和最大输入长度等配置。
- 在 `training/model_train.py` 中实现 BERT 微调，记录训练损失与验证指标。
- 每轮在验证集上检查效果，使用事先约定的指标选择最佳模型；根据需要实现早停。
- 将模型与分词器完整导出至 `model/ft_bert_dir/`，核对类别映射，并记录训练配置和数据版本。

**验收标准：** 可按记录复现训练流程；导出模型可被成员 2 和成员 5 加载；模型选择只使用验证集。

### 成员 5：模型评估与集成

- 在 `training/model_eval.py` 中实现完整测试集评估，输出准确率、各类别 Precision/Recall/F1、宏平均 F1 和混淆矩阵。
- 记录模型版本、数据版本、运行设备与推理耗时，整理典型误判；不使用测试集反复调参。
- 接通 `run_pipeline.py` 的数据准备、训练及评估步骤，确保每一步在实际完成后才报告成功。
- 组织前后端与模型联调，汇总正常输入、空输入、文件编码错误及批量输入等验收结果，更新 README。

**验收标准：** 离线流程可执行；评估结果可复核；页面到真实模型的完整链路可演示，问题有记录和负责人。

## 模块交接约定

### 数据与标签

现有 CSV 使用 UTF-8、无表头，每行格式为 `标签,评价文本`。包含逗号的文本按标准 CSV 引号规则读取，不直接用字符串逗号分割。

```csv
0,"送得太慢，饭菜都凉了。"
1,"味道很好，配送也及时。"
```

`model/thy_labels.txt` 当前顺序为：

```text
差评
好评
```

因此 `0 = 差评`、`1 = 好评`。成员 3、4、2、5 必须保持同一映射；训练集用于学习参数，验证集用于调参与选模型，测试集用于最终评估。

### 训练与推理

- 成员 3 向成员 4、5 提供统一的数据集接口，向成员 2 提供共享清洗函数。
- 成员 4 向成员 2、5 交付模型、分词器、标签映射、最大输入长度和预处理约定。
- 后端与离线评估必须使用同一版本的模型、标签、清洗及编码配置。
- `training/config.py` 由成员 4 主维护；其他成员需要更改公共配置时先同步接口影响。

### 前后端接口（已实现）

下列接口位于 `app/prediction.py`，均已完成前后端联调。

| 方法 | 路径 | 请求与用途 |
| --- | --- | --- |
| GET | `/api/v1/` | 服务存活检查，返回 `{"code":200,"message":"API v1"}`；不包含模型是否就绪的信息 |
| GET | `/api/v1/labels` | 获取按类别编号排序的标签列表 |
| POST | `/api/v1/classify` | JSON 的 `text` 字段为字符串或字符串数组 |
| POST | `/api/v1/classify_from_file` | 表单字段 `text_file` 上传 UTF-8 TXT，每行一条评价（前端暂未调用） |

文本请求示例：

```json
{"text": ["味道很好，配送及时。", "饭菜已经凉了。"]}
```

接口实测输出示例（2026-09-23，使用 `model/ft_bert_dir/` 当前权重；这是推理输出，不是测试集评测指标）：

```json
{
  "code": 200,
  "results": [
    {"text": "这家外卖太好吃了，送得也快，强烈推荐", "label": "好评", "confidence": "99.82%", "is_certain": true},
    {"text": "菜是凉的，还少了一份，太失望了", "label": "差评", "confidence": "99.78%", "is_certain": true}
  ]
}
```

结果顺序与输入一致。`confidence` 为百分比字符串，`is_certain` 的阈值为 80%（`confidence >= 0.8`）。错误响应使用 `code` 与 `message`，HTTP 状态码与 `code` 对齐；`text` 缺失或类型不符返回 400。标签接口返回 `{"code":200,"results":["差评","好评"]}`。

**尚未实现：** `GET /api/v1/model-info`——前端模型报告页期望它返回模型版本、数据集规模、四项指标、混淆矩阵与推理耗时，当前该区域显示「待接入」。

## 开发顺序

1. **统一约定：** 五人确认数据格式、标签映射、接口字段和各自负责范围。
2. **并行开发：** 成员 1、2 开发页面与接口；成员 3 完成数据处理；成员 4、5 确定训练、验证和评估接口。
3. **模型交付：** 成员 4 使用成员 3 的数据集训练并导出模型，成员 5 独立评估。
4. **完整联调：** 成员 2 接入模型，成员 1 接入真实接口，成员 5 组织验收；各成员修复自己模块的问题。

## 环境与运行说明

### 依赖

`requirements.txt` 目前只列出 Flask、pandas、pytest 和 requests；**实际运行还需要 PyTorch、Transformers 和 jieba，尚未补入**，其他机器按现有 `requirements.txt` 安装无法启动服务。

本机已验证可用的组合（2026-09-23 完成前后端联调）：

| 依赖 | 版本 |
| --- | --- |
| Python | 3.12.14 |
| Flask | 3.1.3 |
| torch | 2.14.0+cu130 |
| transformers | 5.17.0 |
| jieba | 0.42.1 |
| pandas | 3.0.5 |

**待办：** 补齐 `requirements.txt` 并统一团队 Python 与 CPU/CUDA 版本；在此之前请按上表使用同一套版本另建环境（conda 或 venv 均可）。

### 启动后端（127.0.0.1:8000）

```powershell
python wsgi.py
```

`wsgi.py` 是后端启动入口：直接执行即启动开发服务器；模块级 `app = create_app()` 也可被生产服务器引用（如 `gunicorn -w 2 'wsgi:app' -b 0.0.0.0:8000`，本机未验证）。应用启动时会加载 `model/ft_bert_dir/` 下约 400MB 的 BERT 权重，请等待数秒后再发请求。

服务是否就绪：

```powershell
curl.exe -s http://127.0.0.1:8000/api/v1/
# 期望输出 {"code":200,"message":"API v1"}
```

### 启动前端（127.0.0.1:5173）

```powershell
cd frontend
npm install
npm run dev
```

`vite.config.js` 已将 `/api` 代理到 `http://127.0.0.1:8000`，前端无需额外处理跨域。端口被 `strictPort: true` 固定：若 5173 已被占用，`npm run dev` 会直接报 `Error: Port 5173 is already in use` 并退出（不会自动换端口），需先释放该端口。

### 联调：让页面调用真实模型

前端默认处于**演示模式**——`VITE_USE_MOCK` 未设置时即按 mock 处理，页面展示的是前端本地构造的示例结果，**不会请求后端**。首次联调：

```powershell
cd frontend
copy .env.example .env
```

把 `.env` 中的 `VITE_USE_MOCK` 改为 `false`，重启 `npm run dev`。页面右上角显示「模型已连接」即表示链路已打通；点击「开始分析」后，评价明细中的标签与置信度即为 BERT 的真实推理结果。`.env` 已在 `.gitignore` 中，不会被提交。

### 离线训练流程

```powershell
python run_pipeline.py
```

- 第 1 步会实际执行 `training/model_train.py` 的 `train()`：读取训练集与验证集，微调 BERT 并逐轮打印验证集准确率，最后把模型与分词器导出到 `model/ft_bert_dir/`。该步骤耗时较长。
- 第 2 步的评估尚未接入，目前只输出阶段提示，不会生成评估结果。

## 团队协作

- 从 `main` 创建自己的功能分支，例如 `feat/frontend`、`feat/backend`、`feat/data`、`feat/training`、`feat/evaluation`，通过 Gitee Pull Request 合并。
- 每次提交聚焦一个任务，说明修改内容、交接影响和验证方式；功能负责人同步补充相关验证。
- 涉及共享清洗、配置、标签或 API 格式的变更，先与使用方确认并同步更新文档。
- 文本、代码和 CSV 统一使用 UTF-8。模型资源通过团队约定的位置共享，不提交权重、虚拟环境、依赖目录、缓存和本地密钥。
- 数据集变更由成员 3 统一管理并记录版本；README 与最终联调记录由成员 5 汇总，其余成员提供本模块说明。
