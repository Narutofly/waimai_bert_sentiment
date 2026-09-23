<script setup>
import AppIcon from './AppIcon.vue'
import { DEMO_MODE } from '../services/sentiment.js'

const datasets = [
  { label: '训练集', value: 9575, percent: 100 },
  { label: '验证集', value: 1197, percent: 12.5 },
  { label: '测试集', value: 1197, percent: 12.5 },
]
const pipeline = [
  { icon: 'code', label: '文本清洗', detail: '移除噪声字符' },
  { icon: 'bubble', label: 'BERT 分词', detail: '最长 32 tokens' },
  { icon: 'brain', label: '模型推理', detail: '中文 BERT 二分类' },
  { icon: 'chart', label: '结果输出', detail: '标签与置信度' },
]
</script>

<template>
  <section id="model" class="model-report-section">
    <div class="section-heading model-report-heading">
      <div><span class="section-kicker">03 / MODEL</span><h2>模型说明</h2></div>
      <span class="integration-badge"><i /> {{ DEMO_MODE ? '演示模式 · 尚未连接模型' : '接口模式 · 待联调验收' }}</span>
    </div>
    <div class="model-hero-card">
      <div class="model-copy">
        <span class="model-chip"><AppIcon name="spark" /> BERT SENTIMENT</span>
        <h2>中文 BERT，专注外卖评价二分类</h2>
        <p>每条评价只有一个预测标签：0 代表差评，1 代表好评。混合、反讽等表达仍会得到二分类结果，需要结合原文理解。低置信度提醒不是第三个类别。</p>
        <div class="model-tags"><span>bert-base-chinese</span><span>0 差评 / 1 好评</span><span>演示与真实结果分开标识</span></div>
      </div>
      <div class="pipeline" aria-label="模型推理流程">
        <div v-for="(step, index) in pipeline" :key="step.label" class="pipeline-step">
          <span><AppIcon :name="step.icon" /></span>
          <div><b>{{ step.label }}</b><small>{{ step.detail }}</small></div>
          <i v-if="index < pipeline.length - 1">→</i>
        </div>
      </div>
    </div>
    <div class="model-report-grid">
      <article class="dataset-card app-card">
        <div class="report-card-heading"><div class="card-icon yellow"><AppIcon name="database" /></div><div><h3>数据集结构</h3><p>初始数据快照 · 2026-09-23 · 非实时统计</p></div></div>
        <div class="dataset-total"><strong>11,969</strong><span>总样本</span><small>训练 / 验证 / 测试</small></div>
        <div class="dataset-bars">
          <div v-for="dataset in datasets" :key="dataset.label"><span><b>{{ dataset.label }}</b><small>{{ dataset.value.toLocaleString() }} 条</small></span><i><em :style="{ width: `${dataset.percent}%` }" /></i></div>
        </div>
        <p class="dataset-note"><AppIcon name="alert" /> 标签比例约为 2:1，最终报告应同时展示 Precision、Recall、F1 和混淆矩阵。</p>
      </article>
      <article class="metrics-card app-card">
        <div class="report-card-heading"><div class="card-icon dark"><AppIcon name="chart" /></div><div><h3>测试集指标</h3><p>等待后端评估产物</p></div><span class="pending-badge">待接入</span></div>
        <div class="metric-placeholders">
          <div><span>Accuracy</span><strong>—</strong><small>准确率</small></div>
          <div><span>Precision</span><strong>—</strong><small>精确率</small></div>
          <div><span>Recall</span><strong>—</strong><small>召回率</small></div>
          <div><span>F1 Score</span><strong>—</strong><small>综合指标</small></div>
        </div>
        <div class="metrics-contract"><span><AppIcon name="chart" /> 指标尚未发布</span><p>测试集准确率与单条评价的置信度含义不同，正式评估完成后将在这里展示。</p></div>
      </article>
    </div>
  </section>
</template>
