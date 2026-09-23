# 外卖评价情感分析

基于中文 BERT 的外卖评价二分类项目，目标是将评价识别为「差评」或「好评」，并通过后端接口和前端页面展示分析结果。

项目仓库：[Gitee / waimai_bert_sentiment](https://gitee.com/whoamber/waimai_bert_sentiment)。

项目已进入前后端联调阶段：后端可加载微调模型提供推理接口，前端页面可调用真实接口展示结果。以下分工基于现有目录，不额外拆分项目架构；成员 1～5 可替换为实际姓名。

## 当前进度

已完成：

- `data/raw/` 下三个 CSV 就绪，共 11,969 条：训练集 9,575、验证集 1,197、测试集 1,197；标签为差评 `0` / 好评 `1`，比例约 2:1，无缺失文本，各集合内部无重复样本。
- `common/preprocess.py` 提供训练与推理共用的清洗函数 `clean_text_for_bert`（HTML 标签、Emoji、控制字符清理与 Unicode 归一化）。
- `training/dataset.py` 完成语料读取与分词编码；`training/model_train.py` 完成 BERT 微调（冻结 embedding 与前 3 层），逐轮打印验证集准确率，并把模型与分词器导出到 `model/ft_bert_dir/`。基座模型 `model/google-bert/bert-base-chinese/` 就位后已实跑通过（GPU）。
- `training/model_eval.py` 完成**全量测试集评估**：1,197 条按 CSV 原始顺序批处理，不抽样、不 shuffle；输出准确率、各类别 Precision/Recall/F1 与支持数、宏平均 F1、加权 F1、混淆矩阵，并整理全部误判、标注典型误判口径（成员 5）。
- `run_pipeline.py` 已接通数据准备、训练、评估三步，每步验证产物之后才报告完成，退出码区分完成（0）/ 失败（1）/ 跳过（3）（成员 5）。
- `app/` 提供 Flask 应用工厂与 4 个推理接口，模型与分词器延迟加载并在进程内复用；启动入口为 `wsgi.py`。
- `frontend/` 为 Vue 3 + Vite 页面，支持文本输入与 TXT 导入、批量分析、筛选排序、置信度分布和 CSV 导出。
- 前后端已联通：页面可调用真实模型并展示标签与置信度。

尚未完成：

- `training/model_eval.py` 的报告落盘（`logs/eval/<run_id>/` 下的 `metrics.json`、`report.md`、`misclassifications.json`）、模型与数据版本指纹、Cohen's kappa 与耗时明细尚未实现。评估目前只在终端输出，因此 `docs/eval_report.md` 仍无法定稿。
- `requirements.txt` 未实测 torch 的 CUDA 轮子与其余依赖的组合可用性；`pip install -r requirements.txt` 装到的可能是数 GB 的 CUDA 版 torch（见「依赖」）。
- 前端模型报告页期望的 `GET /api/v1/model-info` 尚未实现，页面该区域显示「待接入」。
- 前端「导入 TXT」在浏览器本地读取后调用 `/api/v1/classify`，后端 `classify_from_file` 接口暂无调用方。
- 评估指标不在此处手工填写，以脚本产出为准。

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
│   ├── pre/                     # 预处理产物，由数据准备步骤再生，不纳入 Git
│   └── raw/                     # UTF-8、无表头，每行 标签,"评价文本"
│       ├── train.csv            # 训练集 9,575 条
│       ├── valid.csv            # 验证集 1,197 条
│       └── test.csv             # 测试集 1,197 条
├── docs/
│   └── eval_report.md           # 测试集评估定稿报告（唯一入库的评估产物）
├── frontend/                    # 前端：Vue 3 + Vite
│   ├── src/
│   │   ├── App.vue              # 页面框架、状态汇总与接口调用
│   │   ├── main.js
│   │   ├── style.css
│   │   ├── desktop.css
│   │   ├── welcome.css
│   │   ├── components/          # AnalyzerCard、ReviewFeed、ReviewDetail、InsightPanel、
│   │   │                        #   ModelReport、WelcomeScene、AppIcon
│   │   └── services/            # sentiment.js、binary.js、reviewView.js
│   ├── tests/                   # binary.test.js、reviewView.test.js
│   ├── public/images/           # 角色形象等静态资源
│   ├── .env.example             # 接口地址与 mock 开关示例
│   ├── index.html
│   ├── package.json
│   └── vite.config.js           # 5173 端口与 /api 代理
├── logs/                        # 运行产物，不纳入 Git
│   └── eval/<run_id>/           # 每次评估的 metrics.json / report.md / misclassifications.json
├── model/                       # 本地模型资源，不纳入 Git
│   ├── google-bert/
│   │   └── bert-base-chinese/   # 预训练模型与分词器
│   ├── ft_bert_dir/             # 微调导出的模型与分词器（约 400MB）
│   └── thy_labels.txt           # 类别编号与中文标签映射
├── tests/
│   └── test_model_eval_report.py  # 报告渲染与误判整理的单元测试（不需要模型）
├── training/
│   ├── __init__.py
│   ├── config.py                # 数据与模型路径配置
│   ├── dataset.py               # 语料读取、清洗与分词编码
│   ├── model_train.py           # 模型训练及训练期间验证
│   └── model_eval.py            # 全量测试集评估、指标渲染与误判整理
├── conftest.py                  # 让 pytest 能找到项目模块
├── requirements.txt             # Python 依赖（版本精确锁定）
├── run_pipeline.py              # 离线流程入口
├── wsgi.py                      # 后端启动入口
└── README.md
```

`data/pre/`、`model/ft_bert_dir/` 与 `logs/eval/<run_id>/` 都是**本地产物，不纳入 Git**。
`data/pre/` 由数据准备步骤自动创建，`logs/eval/<run_id>/` 由评估步骤自动创建，都不需要手工准备；
`model/ft_bert_dir/` 由成员 4 训练产出，干净检出上没有它时评估会如实报「跳过」。

## 五人分工

以下是立项时的任务划分，用于说明各成员的负责范围；各部分的完成情况见上方「当前进度」。

| 成员 | 岗位 | 主要负责范围 | 核心交付物 |
| --- | --- | --- | --- |
| 成员 1 | 前端开发 | `frontend/` | Vue 3 页面、文本与文件输入、结果展示、接口联调 |
| 成员 2 | 后端开发 | `app/` | Flask 应用、模型加载、推理接口、参数校验与错误处理 |
| 成员 3 | 数据处理 | `common/`、`training/dataset.py`、`data/` | 数据检查、共享清洗函数、训练与评估使用的数据集 |
| 成员 4 | 模型训练 | `training/model_train.py`、`training/config.py` | BERT 微调、每轮验证、最佳模型及分词器导出 |
| 成员 5 | 模型评估与集成 | `training/model_eval.py`、`run_pipeline.py`、`README.md`、`docs/` | 测试集评估报告（`docs/eval_report.md`）、完整离线流程、联调与验收记录 |

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

评估步骤（成员 5）已可运行。它依赖成员 3 的 `common/preprocess.py` 与成员 4 的 `model/ft_bert_dir/`：
清洗模块缺失属于真实失败（退出码 1），模型目录缺失属于依赖缺失，报「跳过」（退出码 3）。

## 环境与运行说明

### 依赖

Python 依赖以 `requirements.txt` 为准，版本已精确锁定。

`requirements.txt` 已锁定 Flask、pandas、numpy、scikit-learn、pytest，以及 PyTorch 与 Transformers。注意 PyPI 上默认的 `torch` 轮子自带 CUDA、体积数 GB；只用 CPU 的机器请按该文件内注释改用官方 CPU 源安装。**项目不需要 jieba** —— 中文 BERT 为字级分词，清洗由 `common/preprocess.py` 用正则实现。

本机已验证可用的组合（2026-09-23 完成前后端联调）：

| 依赖 | 版本 |
| --- | --- |
| Python | 3.12.14 |
| Flask | 3.1.3 |
| torch | 2.14.0+cu130 |
| transformers | 5.17.0 |
| pandas | 3.0.5 |

仓库 `.venv` 另实测通过一组（Python 3.13.15）：`torch 2.14.0+cu126`、`transformers 5.17.0`、`Flask 3.1.3`、`pandas 3.0.5`、`scikit-learn 1.9.1`、`pytest 9.1.1`，不含 jieba；GPU 为 RTX 3060 Laptop（6GB），10 轮微调约 27 秒/轮。

**待办：** 统一团队的 Python 与 CUDA 版本。`requirements.txt` 已锁定版本，直接按它安装即可；CPU-only 的机器按该文件内注释改用官方 CPU 源。

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
.\.venv\Scripts\python.exe run_pipeline.py
```

三步依次执行，每步都会先验证产物真的落盘，才报告完成：

1. **数据准备** —— 按 CSV 规则解析 `data/raw/*.csv`（文本字段带引号且自身含逗号，不能直接按逗号切分），
   清洗后写出 `data/pre/tmf_train.txt` 与 `data/pre/tmf_valid.txt`，并校验行数。
2. **训练** —— 执行 `training/model_train.py` 的 `train()`：读取训练集与验证集，微调 BERT
   并逐轮打印验证集准确率，最后把模型与分词器导出到 `model/ft_bert_dir/`。
   该步骤耗时最长（本机 GPU 实测约 27 秒/轮 × 10 轮）。基座模型
   `model/google-bert/bert-base-chinese/` 缺失时本步报「跳过」而不是失败。
3. **评估** —— 全量评估 `model/ft_bert_dir/`，输出指标表与混淆矩阵。

### 退出码

脚本退出码即结论，不要只看屏幕输出：

| 退出码 | 含义 |
| --- | --- |
| 0 | 三步全部真的完成 |
| 1 | 有步骤真实失败（异常或产物缺失） |
| 3 | 没有失败，但有步骤因「尚未实现」或「依赖缺失」被跳过 |

被跳过的步骤**不会**返回 0，避免出现「没做完却报告成功」。只要有任一步被跳过
（含 `--eval-only`、`--skip-prep` 这类**主动跳过**）就返回 3 —— 它回答的是
「整条流水线是否真的全部跑完」，而不是「这次请求的工作是否做完了」。
若只关心评估本身是否成功，用 `python -m training.model_eval`：它只跑评估、
不跳过任何步骤，返回 0/1。

常用参数：

```powershell
# 只评估已交付的模型，跳过数据准备与训练
.\.venv\Scripts\python.exe run_pipeline.py --eval-only

# 复用已有预处理结果，只重跑训练与评估
.\.venv\Scripts\python.exe run_pipeline.py --skip-prep

# 单独跑评估（覆盖范围等价于 --eval-only），可临时覆盖批大小与最大长度
.\.venv\Scripts\python.exe -m training.model_eval --batch-size 64 --max-length 64
```

`--eval-only` 与 `--skip-prep` 同时给出时以 `--eval-only` 为准。`max_length` 默认 32，
与 `WaimaiDataset(max_len=32)` 及在线推理一致；改大只会把截断点推后，离线指标与线上口径
将不再一致，除有明确理由外不要改。

在没有模型的机器上，可以先用单元测试验证报告渲染与误判整理逻辑（不需要 torch）：

```powershell
.\.venv\Scripts\python.exe -m pytest tests -v
```

## 模型评估与复核

评估由 `training/model_eval.py` 实现，负责人成员 5。**评估结果全部由脚本产出，文档中不手工填写任何指标。**

运行方式：

```powershell
.\.venv\Scripts\python.exe run_pipeline.py --eval-only
.\.venv\Scripts\python.exe -m training.model_eval
```

### 评估口径

- **跑全量测试集**（当前 1197 条），按 CSV 原始顺序批处理，**不抽样、不 shuffle**。
  早期版本曾用「随机抽 16 条 × 128 次」，既未覆盖全量、又因缺少随机种子无法复核，已整体替换。
- **测试集只用于最终评估，不参与任何调参。** 调参与选模型一律使用 `valid.csv`（成员 4）。
  测试集指标不允许作为反复调参的依据。
- 预处理沿用成员 3 的 `common/preprocess.py`。该模块缺失时评估**直接失败**而不是降级跳过清洗，
  以保证离线指标与后端（成员 2）推理口径一致。

### 记录内容

| 类别 | 具体字段 |
| --- | --- |
| 指标 | 准确率、各类别 Precision/Recall/F1 与支持数、宏平均 F1、加权 F1、Cohen's kappa、混淆矩阵 |
| 模型版本 | `model/ft_bert_dir` 目录指纹（12 位 `version_id`）、`config.json`/`tokenizer_config.json`/`vocab.txt` 的 sha256、权重文件名与字节数 |
| 基座模型 | `model/google-bert/bert-base-chinese` 目录指纹与 `config.json` sha256 |
| 数据版本 | `train.csv`/`valid.csv`/`test.csv` 的 sha256、行数与标签分布 |
| 代码版本 | git commit 与工作区是否 dirty |
| 运行设备 | 设备类型、CUDA 是否可用、GPU 名称、各依赖版本、`max_length` |
| 推理耗时 | 清洗、分词、前向推理、端到端各自的每样本耗时与吞吐；单批耗时的 mean/p50/p90/p95/p99/max，并保留逐批原始值 |
| 典型误判 | 全部误判明细 + 按多种口径挑出的典型样本 |

上表是报告的**目标口径**，不是当前已具备的能力。目前已实现并在运行时打印的是：准确率、
各类别 Precision/Recall/F1 与支持数、宏平均 F1、加权 F1、混淆矩阵，以及全部误判的明细与
典型误判口径标注。**尚未实现**的是：Cohen's kappa、模型与数据各类指纹（`version_id`、
sha256）、逐批耗时明细，以及三个产物文件（`metrics.json`/`report.md`/`misclassifications.json`）
的落盘 —— 评估跑完只在终端输出，不写 `logs/eval/`。因此 `docs/eval_report.md` 仍无法定稿。

耗时口径：先跑 3 个批次预热并丢弃结果，再全量正式计时，以排除 CUDA 首次调用开销；
评估使用 `padding='max_length'`，保证每次运行张量形状一致、耗时可比。
**延迟与机器强相关，只能同机前后对比，不可跨机器比较。**

### 复核方式

每次运行产出一个 `run_id`（时间戳），产物位于 `logs/eval/<run_id>/`（该目录不纳入 Git）：

- `metrics.json` — 全部结构化指标、版本指纹、耗时明细与逐批原始耗时
- `report.md` — 中文可读报告：摘要、指标表、混淆矩阵、耗时、典型误判、告警与已知限制
- `misclassifications.json` — 全部误判，含 CSV 行号、原文、真实/预测标签、置信度与选取口径

复核步骤：

1. 取报告中记录的 `data_version` 中 test.csv 的 sha256，与当前文件比对，确认是同一份测试集。
2. 取 `model_version_id` 与 `config.json` 的 sha256，确认是同一个模型。
3. 用相同的 `batch_size` 与 `max_length` 重跑，指标应当完全一致（全量评估本身是确定性的；
   耗时会随机器负载浮动，属正常）。
4. 按 `misclassifications.json` 里的 `line_number` 回到 `data/raw/test.csv` 对应行核对原文。

指标为 0 或很低的常见原因：模型尚未训练、标签映射与 `thy_labels.txt` 不一致、
或清洗函数与训练时使用的版本不同。

### 典型误判的选取规则

按多种口径取并集（按行号去重，上限 30 条）后写入明细，报告正文展示前 10 条：

| 口径 | 上限 | 关注点 |
| --- | --- | --- |
| 各真实类别的误判 | 每类 5 条 | 保证每个混淆方向都有代表 |
| 高置信度误判 | 10 条 | 模型很自信却错了，优先怀疑测试集标注噪声 |
| 低置信度误判 | 10 条 | 贴近决策边界的难例 |
| 最长文本误判 | 5 条 | 是否因 `max_length` 截断丢了关键信息 |
| 最短文本误判 | 5 条 | 信息量不足 |

入库的定稿报告见 [`docs/eval_report.md`](docs/eval_report.md)（目前仍为待评估状态：模型已就绪且能跑出指标，但报告落盘功能尚未实现，故无法定稿）。

### 已知限制

- 标签文件 `model/thy_labels.txt` 缺失时，报告使用 `类别0`/`类别1` 占位名并在告警中说明，
  **不默认推断 0=差评、1=好评**；此时请以成员 4 导出的标签文件为准。
- `reached_max_length` 表示文本 token 数达到上限（可能被截断），不是严格意义上的「一定被截断」。
- 延迟数据仅作同机冒烟参考。
- 本评估只覆盖离线测试集，线上表现仍需按下节的集成验收逐项确认。

## 集成验收记录

负责人：成员 5；各项的实测人见「负责人」列。**下表尚未逐项实测填写，不得预填任何编造的实测结果。**

| 验收项 | 输入 | 期望结果 | 实际结果 | 结论 | 问题编号 | 负责人 |
| --- | --- | --- | --- | --- | --- | --- |
| 正常输入（单条） | `{"text": "味道很好，配送及时。"}` | 返回标签与置信度，`code=200` | 待联调 | 待联调 | — | 成员 2 |
| 正常输入（多条） | `text` 为 3 条字符串的数组 | 结果顺序与输入一致 | 待联调 | 待联调 | — | 成员 2 |
| **空输入** | `{"text": ""}`、`{"text": []}`、空 TXT 文件 | 明确错误响应，不返回 500 | 待联调 | 待联调 | — | 成员 2 |
| **文件编码错误** | 非 UTF-8（如 GBK）编码的 TXT | 明确提示编码错误，不 500 | 待联调 | 待联调 | — | 成员 2 |
| **批量输入** | 每行一条评价的 UTF-8 TXT | 全部返回且顺序一致，条数与输入相同 | 待联调 | 待联调 | — | 成员 1、成员 2 |
| 超长文本 | 超过 `max_length` 的评价 | 截断后正常返回，不报错 | 待联调 | 待联调 | — | 成员 2、成员 4 |
| 模型未就绪 | 移除 `model/ft_bert_dir/` 后启动 | `/api/v1/` 能区分模型是否就绪 | 待联调 | 待联调 | — | 成员 2 |
| 离线与在线一致性 | 同一段文本分别走接口与离线推理 | 标签与置信度一致 | 待联调 | 待联调 | — | 成员 2、成员 5 |
| 页面到模型全链路 | 前端输入 → 后端 → 真实模型 | 页面展示真实预测结果 | 待联调 | 待联调 | — | 成员 1、成员 5 |

### 问题清单

规则：上表中结论为「不通过」的每一项，都必须在此登记一个非空的问题编号。

| 问题编号 | 现象 | 影响 | 负责人 | 状态 | 关联提交 |
| --- | --- | --- | --- | --- | --- |
| — | 联调尚未开始，暂无问题记录 | — | — | — | — |

## 团队协作

- 从 `main` 创建自己的功能分支，例如 `feat/frontend`、`feat/backend`、`feat/data`、`feat/training`、`feat/evaluation`，通过 Gitee Pull Request 合并。
- 每次提交聚焦一个任务，说明修改内容、交接影响和验证方式；功能负责人同步补充相关验证。
- 涉及共享清洗、配置、标签或 API 格式的变更，先与使用方确认并同步更新文档。
- 文本、代码和 CSV 统一使用 UTF-8。模型资源通过团队约定的位置共享，不提交权重、虚拟环境、依赖目录、缓存和本地密钥。
- 数据集变更由成员 3 统一管理并记录版本；README 与最终联调记录由成员 5 汇总，其余成员提供本模块说明。
