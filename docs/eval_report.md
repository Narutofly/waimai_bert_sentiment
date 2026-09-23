# 测试集评估报告（定稿）

> **当前状态：待评估 —— 本文件尚无任何指标数据。**
>
> **阻塞项是报告功能未实现，而非前置条件缺失。**
>
> `training/model_eval.py` 目前只有 `evaluate()` 的分批前向评测（输出准确率与单样本耗时），
> 以及一组**尚未被调用**的报告渲染与整理函数 —— 混淆矩阵、指标表、典型误判整理、
> 模型目录指纹、依赖前置检查。
>
> 这些函数的规格由 `tests/test_model_eval_report.py` 覆盖，**14 项已全部通过**；
> 但**尚无任何代码把它们串起来**产出 `report.md` / `metrics.json`，
> 数据 sha256、运行环境与耗时拆解等也仍未实现，因此依然无法产出本文件。
> 报告生成部分是当前唯一的阻塞项。
>
> 两个前置条件当前**已具备**：
>
> 1. `common/preprocess.py` 中的 `clean_text_for_bert` —— 已随团队代码合入
> 2. `model/ft_bert_dir/` 下的 2 分类模型与分词器 —— 本地已存在
>    （`classifier.weight [2, 768]`、`model.safetensors` 409 MB、`tokenizer.json`）
>
> 需要注意：基座模型目录 `model/google-bert/bert-base-chinese`（即 `Config.bert_model_dir`）
> 当前缺失，`training/model_train.py` 的 `train()` 因此无法重跑。这影响**复现训练**，
> 不影响对已有 `model/ft_bert_dir` 的评测。
>
> 评估在缺少前置条件时**会明确失败**，不会降级产出一份看起来权威、实则与后端口径不一致的报告。
> 待报告功能实现后，由成员 5 运行评估并按下述格式更新本文件。

## 报告来源

| 项 | 值 |
| --- | --- |
| run_id | 待填写 |
| 生成时间 | 待填写 |
| 原始产物 | `logs/eval/<run_id>/`（不纳入 Git） |
| 生成命令 | `.\.venv\Scripts\python.exe run_pipeline.py --eval-only`（该开关**尚未实现**：`run_pipeline.py` 目前无参数解析，见上方阻塞项） |

本文件是从 `logs/eval/<run_id>/report.md` 誊抄的定稿摘要，供不运行流程的人直接查看。
**原始证据以 `logs/eval/<run_id>/metrics.json` 为准**，任何指标都应能在那里逐字段复核。

## 指标

待填写。更新时需包含：准确率、各类别 Precision/Recall/F1 与支持数、宏平均 F1、加权 F1、
Cohen's kappa，以及混淆矩阵。

## 版本记录

待填写。需包含：模型目录指纹与 `config.json` sha256、权重文件字节数、基座模型指纹、
三个 CSV 的 sha256 与标签分布、git commit 与工作区是否 dirty。

缺少版本记录的报告无法复核 —— 无法确认指标对应的是哪个模型、哪份数据。

## 运行环境与耗时

待填写。需包含：设备类型与 GPU 名称、依赖版本、`max_length` 与批大小、
清洗/分词/前向推理/端到端的每样本耗时与吞吐。

延迟与机器强相关，只作同机冒烟参考，**不可跨机器比较**。

## 典型误判

待填写。需包含按各行号回到 `data/raw/test.csv` 可核对的原文、真实标签、预测标签与置信度。
选取规则见 README「典型误判的选取规则」。

## 已知限制

- 标签文件缺失时报告使用 `类别0`/`类别1` 占位名，不推断 `0=差评、1=好评`。
- `reached_max_length` 表示 token 数达到上限（可能被截断），不是严格的「一定被截断」。
- 本报告只覆盖离线测试集，线上表现需按 README 的集成验收记录逐项确认。
