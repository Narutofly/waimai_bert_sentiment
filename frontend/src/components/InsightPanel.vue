<script setup>
import { computed } from 'vue'
import AppIcon from './AppIcon.vue'

const props = defineProps({ summary: { type: Object, required: true }, buckets: { type: Array, required: true }, busy: Boolean, elapsed: String, demoMode: Boolean })
const emit = defineEmits(['filter'])
const donutStyle = computed(() => ({ '--positive-rate': `${Math.max(0, Math.min(100, props.summary.positiveRate)) * 3.6}deg` }))
const maxBucket = computed(() => Math.max(1, ...props.buckets.map((item) => item.count)))
const insight = computed(() => {
  if (!props.summary.total) return '完成分析后，这里会给出本次评价的经营提示。'
  if (props.summary.review) return `${props.summary.review} 条预测被标记为低置信度，建议结合原文人工判断。`
  if (props.summary.negative) return `${props.summary.negative} 条评价被判为差评，点击差评卡片查看原文。`
  return '本次结果均为好评，可以浏览原文了解具体反馈。'
})
</script>

<template>
  <article class="app-card insight-card" :aria-busy="busy">
    <div class="card-title-row">
      <div class="card-icon dark"><AppIcon name="chart" /></div>
      <div><h3>本次评价洞察</h3><p>{{ summary.total ? `已分析 ${summary.total} 条${elapsed ? ` · 用时 ${elapsed}s` : ''}` : '等待提交评价' }}</p></div>
      <span class="live-tag"><i /> {{ demoMode ? '模拟演示' : '二分类结果' }}</span>
    </div>
    <Transition name="panel" mode="out-in">
    <div v-if="busy" key="loading" class="insight-loading" role="status"><div class="scan-ticket"><AppIcon name="bubble" /><i /><i /><i /><span class="scan-line" /></div><strong>{{ demoMode ? '正在生成演示结果' : '正在等待模型响应' }}</strong><span>评价已提交 · 完成后自动更新结果</span></div>
    <div v-else key="results" class="insight-content">
      <div class="metrics-grid">
        <button :disabled="!summary.total" @click="emit('filter', 'all')"><span>全部评价</span><strong>{{ summary.total }}</strong><small>查看全部 ↗</small></button>
        <button class="metric-positive" :disabled="!summary.total" @click="emit('filter', 'positive')"><span>好评 · 1</span><strong>{{ summary.positive }}</strong><small>查看好评 ↗</small></button>
        <button class="metric-negative" :disabled="!summary.total" @click="emit('filter', 'negative')"><span>差评 · 0</span><strong>{{ summary.negative }}</strong><small>查看差评 ↗</small></button>
      </div>
      <button class="review-strip" :disabled="!summary.scored" @click="emit('filter', 'review')"><AppIcon name="alert" /><span>{{ summary.scored ? `${summary.review} 条低置信度结果，建议人工复核` : '分析后查看置信度及人工复核提示' }}</span><AppIcon name="chevron" /></button>
      <div class="charts-row">
        <div class="donut-block"><div class="donut" :class="{ 'donut-empty': !summary.total }" :style="donutStyle"><div><strong>{{ summary.total ? summary.positiveRate.toFixed(0) + '%' : '—' }}</strong><span>预测好评占比</span></div></div><div class="donut-legend"><span><i class="good" />好评 {{ summary.positive }}</span><span><i class="bad" />差评 {{ summary.negative }}</span></div></div>
        <div v-if="summary.scored" class="histogram-block"><div class="mini-heading"><span>置信度分布</span><b>平均 {{ summary.average.toFixed(1) }}%</b></div><div class="histogram"><div v-for="bucket in buckets" :key="bucket.label" class="histogram-column"><span>{{ bucket.count || '' }}</span><i :style="{ height: `${bucket.count / maxBucket * 100}%` }" /><small>{{ bucket.label }}</small></div></div><p class="confidence-caption">{{ summary.scored }} 条提供置信度 · 非模型准确率</p></div>
        <div v-else class="score-empty"><AppIcon name="chart" /><strong>先看结果，再看原文</strong><p>好评与差评各有原因，点击统计卡片筛选查看。</p></div>
      </div>
      <div class="ai-tip"><span><AppIcon name="bubble" /></span><div><b>阅读提示</b><p>{{ insight }}</p></div></div>
    </div>
    </Transition>
  </article>
</template>
