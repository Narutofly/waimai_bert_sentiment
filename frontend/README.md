# 听见外卖 · 评论洞察前端

面向外卖评价情感分析课程项目的 Vue 3 前端原型。视觉语言参考主流外卖 App 的暖黄色顶栏、卡片评价流与移动端底部导航，同时保留原创名称、标志和界面结构。

## 已实现

- 单条、多行评价和 UTF-8 TXT 文件输入。
- 好评、差评、平均置信度和低置信度复核统计。
- 情感占比环形图和置信度分布图。
- 配送、口味、包装、分量、服务五类评价主题聚合。
- 评价关键词搜索、分类筛选和置信度排序。
- 导出当前筛选结果为 UTF-8 CSV。
- 数据集结构、推理链路和真实评估指标接入位的模型报告。
- 桌面端双栏与移动端 App 式单栏布局。
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
│   ├── TopicPanel.vue            评价主题聚合和代表评论
│   ├── ReviewFeed.vue            App 式评价流、筛选和导出
│   ├── ModelReport.vue           数据集、推理链路和指标接入位
│   └── AppIcon.vue               项目内 SVG 图标
├── services/sentiment.js         演示分类与真实接口适配
└── style.css                     视觉系统与响应式布局
```

模型指标页目前展示接口占位说明。后端提供模型版本、测试集 Accuracy、Precision、Recall、F1 和混淆矩阵后，再接入真实指标。
