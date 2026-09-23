<script setup>
import { computed } from 'vue'
import AppIcon from './AppIcon.vue'

const props = defineProps({ summary: { type: Object, required: true }, buckets: { type: Array, required: true }, busy: Boolean, elapsed: String })
const donutStyle = computed(() => ({ '--positive-rate': `${Math.max(0, Math.min(100, props.summary.positiveRate)) * 3.6}deg` }))
const maxBucket = computed(() => Math.max(1, ...props.buckets.map((item) => item.count)))
const insight = computed(() => {
  if (!props.summary.total) return '完成分析后，这里会给出本次评价的经营提示。'
  if (props.summary.review) return `优先复核 ${props.summary.review} 条低置信度评价，再处理明确差评。`
  if (props.summary.negative) return `发现 ${props.summary.negative} 条明确差评，建议结合原文逐条跟进。`
  return '本次评价整体积极，可以继续关注高频表扬内容。'
})
</script>

<template>
  <article class="app-card insight-card" :aria-busy="busy">
    <div class="card-title-row">
      <div class="card-icon dark"><AppIcon name="chart" /></div>
      <div><h3>本次评价洞察</h3><p>{{ summary.total ? `已分析 ${summary.total} 条${elapsed ? ` · 用时 ${elapsed}s` : ''}` : '等待提交评价' }}</p></div>
      <span class="live-tag"><i /> 实时汇总</span>
    </div>
    <div v-if="busy" class="insight-loading"><div class="loading-bars"><i v-for="i in 5" :key="i" /></div><strong>AI 正在分析情绪</strong><span>批量评价很快就好</span></div>
    <template v-else>
      <div class="metrics-grid">
        <div><span>评价总数</span><strong>{{ summary.total }}</strong><small>本次提交</small></div>
        <div class="metric-positive"><span>好评</span><strong>{{ summary.positive }}</strong><small>{{ summary.total ? summary.positiveRate.toFixed(1) : '0.0' }}%</small></div>
        <div class="metric-negative"><span>差评</span><strong>{{ summary.negative }}</strong><small>需要关注</small></div>
        <div class="metric-review"><span>待复核</span><strong>{{ summary.review }}</strong><small>置信度 &lt; 80%</small></div>
      </div>
      <div class="charts-row">
        <div class="donut-block"><div class="donut" :style="donutStyle"><div><strong>{{ summary.positiveRate.toFixed(0) }}%</strong><span>好评率</span></div></div><div class="donut-legend"><span><i class="good" />好评 {{ summary.positive }}</span><span><i class="bad" />差评 {{ summary.negative }}</span></div></div>
        <div class="histogram-block"><div class="mini-heading"><span>置信度分布</span><b>平均 {{ summary.average.toFixed(1) }}%</b></div><div class="histogram"><div v-for="bucket in buckets" :key="bucket.label" class="histogram-column"><span>{{ bucket.count || '' }}</span><i :style="{ height: `${Math.max(bucket.count ? 16 : 3, bucket.count / maxBucket * 100)}%` }" /><small>{{ bucket.label }}</small></div></div></div>
      </div>
      <div class="ai-tip"><span><AppIcon name="spark" /></span><div><b>AI 经营提示</b><p>{{ insight }}</p></div></div>
    </template>
  </article>
</template>
