<script setup>
import AppIcon from './AppIcon.vue'

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
      <div><span class="section-kicker">04 / MODEL</span><h2>模型报告</h2></div>
      <span class="integration-badge"><i /> 前端接口已就绪</span>
    </div>
    <div class="model-hero-card">
      <div class="model-copy">
        <span class="model-chip"><AppIcon name="spark" /> BERT SENTIMENT</span>
        <h2>中文 BERT，专注外卖评价二分类</h2>
        <p>从评价文本到情感标签，前端只展示接口返回的真实结果。模型指标将在评估脚本导出后接入，不使用虚构分数。</p>
        <div class="model-tags"><span>bert-base-chinese</span><span>好评 / 差评</span><span>复核阈值 &lt; 80%</span></div>
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
        <div class="report-card-heading"><div class="card-icon yellow"><AppIcon name="database" /></div><div><h3>数据集结构</h3><p>仓库当前 CSV 样本规模</p></div></div>
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
        <div class="metrics-contract"><span><AppIcon name="code" /> 建议接口</span><code>GET /api/v1/model-info</code><p>返回模型版本、数据集规模、四项指标、混淆矩阵与推理耗时。</p></div>
      </article>
    </div>
  </section>
</template>
