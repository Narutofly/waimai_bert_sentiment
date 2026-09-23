# 听见外卖 · 评论洞察前端

面向外卖评价情感分析课程项目的 Vue 3 前端原型。视觉语言参考主流外卖 App 的暖黄色顶栏、卡片评价流与移动端底部导航，同时保留原创名称、标志和界面结构。

## 已实现

- 单条、多行评价和 UTF-8 TXT 文件输入。
- 好评、差评、平均置信度和低置信度复核统计。
- 情感占比环形图和置信度分布图。
- 明确对齐二分类标签：0 为差评、1 为好评；低置信度是复核状态。
- 评价关键词搜索、分类筛选和置信度排序。
- 导出当前筛选结果为 UTF-8 CSV。
- 数据集结构、推理链路和真实评估指标接入位的模型报告。
- 桌面端双栏与移动端 App 式单栏布局。
- 点击统计卡筛选、每页 20 条结果、跟随滚动的导航和操作反馈动画。
- 演示模式与真实 Flask 接口模式切换。

## 本地运行

```powershell
npm.cmd install
npm.cmd run dev
```

打开 <http://127.0.0.1:5173>。

项目默认启用演示模式，页面会明确显示“前端演示模式”和“演示数据”。演示分类只用于验证界面交互，不代表 BERT 模型输出。

## 接入真实后端

复制 `.env.example` 为 `.env.local`，修改：

```dotenv
VITE_USE_MOCK=false
VITE_API_BASE=/api/v1
VITE_API_PROXY_TARGET=http://127.0.0.1:8000
```

前端调用以下现有接口契约：

```http
GET  /api/v1/
POST /api/v1/classify
```

分类请求：

```json
{
  "text": ["包装很仔细，送到时还是热的。", "配送太慢，饭都凉了。"]
}
```

分类响应：

```json
{
  "code": 200,
  "results": [
    {
      "text": "包装很仔细，送到时还是热的。",
      "label": "好评",
      "confidence": "96.20%",
      "is_certain": true
    }
  ]
}
```

## 生产构建

```powershell
npm.cmd run build
npm.cmd run preview
```

构建产物输出到 `dist/`。

## 主要文件

```text
src/
├── App.vue                       页面框架、分析状态和结果汇总
├── components/
│   ├── AnalyzerCard.vue          评价输入和 TXT 导入
│   ├── InsightPanel.vue          指标、情感占比和置信度分布
│   ├── ReviewFeed.vue            App 式评价流、筛选和导出
│   ├── ModelReport.vue           数据集、推理链路和指标接入位
│   └── AppIcon.vue               项目内 SVG 图标
├── services/sentiment.js         演示分类与真实接口适配
└── style.css                     视觉系统与响应式布局
```

模型指标页目前展示接口占位说明。后端提供模型版本、测试集 Accuracy、Precision、Recall、F1 和混淆矩阵后，再接入真实指标。

## 二分类接口对齐与本轮改动

以团队 README 的接口约定为依据：每条结果必须包含原始 `text`、`label`、百分比字符串 `confidence` 和布尔值 `is_certain`。标签接受数值 0/1、字符串 "0"/"1" 或中文差评/好评，统一显示为中文；未知标签、缺失概率和批次顺序不一致会报错并保留上次成功结果。复核状态遵循后端 `is_certain`；80% 仅为当前演示阈值。

已撤下原先通过关键词匹配的配送、口味等主题统计；整条评价二分类不能推导出分项情感。保留原文搜索。

请求提供 90 秒超时；TXT 导入检查 UTF-8、2 MB 大小、500 条数量及 100,000 字符上限。CSV 包含 0/1 标签和结果来源，并转义表格公式前缀。

`npm.cmd test` 验证标签映射、置信度、复核状态及批次校验；`npm.cmd run build` 验证生产构建。页面尊重系统减少动画偏好。
