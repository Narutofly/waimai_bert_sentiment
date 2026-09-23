<script setup>
import { computed, ref } from 'vue'
import AppIcon from './AppIcon.vue'

const props = defineProps({ results: { type: Array, required: true }, busy: Boolean })
const search = defineModel('search', { type: String, default: '' })
const emit = defineEmits(['export'])
const activeFilter = ref('all')
const sort = ref('default')
const filters = computed(() => [
  { key: 'all', label: '全部', count: props.results.length },
  { key: 'positive', label: '好评', count: props.results.filter((item) => item.tone === 'positive').length },
  { key: 'negative', label: '差评', count: props.results.filter((item) => item.tone === 'negative').length },
  { key: 'review', label: '待复核', count: props.results.filter((item) => !item.is_certain).length },
])
const visible = computed(() => {
  const keyword = search.value.trim().toLocaleLowerCase()
  let items = props.results.filter((item) => {
    const filterMatch = activeFilter.value === 'all' || activeFilter.value === item.tone || (activeFilter.value === 'review' && !item.is_certain)
    return filterMatch && (!keyword || item.text.toLocaleLowerCase().includes(keyword))
  })
  if (sort.value === 'low') items = [...items].sort((a, b) => a.confidenceValue - b.confidenceValue)
  if (sort.value === 'high') items = [...items].sort((a, b) => b.confidenceValue - a.confidenceValue)
  return items
})
</script>

<template>
  <section id="reviews" class="reviews-section">
    <div class="section-heading reviews-heading"><div><span class="section-kicker">03 / REVIEWS</span><h2>评价明细</h2></div><button class="export-button" type="button" :disabled="!visible.length || busy" @click="emit('export', visible)"><AppIcon name="download" /> 导出当前结果</button></div>
    <div class="review-toolbar">
      <div class="filter-tabs" role="group" aria-label="评价筛选"><button v-for="filter in filters" :key="filter.key" type="button" :class="{ active: activeFilter === filter.key }" :aria-pressed="activeFilter === filter.key" @click="activeFilter = filter.key">{{ filter.label }} <span>{{ filter.count }}</span></button></div>
      <label class="sort-select"><AppIcon name="filter" /><select v-model="sort" aria-label="结果排序"><option value="default">默认排序</option><option value="low">置信度从低到高</option><option value="high">置信度从高到低</option></select></label>
    </div>
    <div v-if="!results.length && !busy" class="empty-reviews"><span><AppIcon name="bubble" /></span><h3>还没有评价结果</h3><p>在上方放入评论并开始分析，结果会像真实外卖 App 的评价流一样展示。</p></div>
    <div v-else class="review-list">
      <article v-for="(item, index) in visible" :key="`${item.text}-${index}`" class="review-item">
        <div class="avatar" :class="item.tone">{{ item.tone === 'positive' ? '赞' : '评' }}</div>
        <div class="review-body">
          <div class="review-author"><div><strong>匿名顾客 {{ String(index + 1).padStart(2, '0') }}</strong><span>来自本次分析</span></div><time>刚刚</time></div>
          <p>{{ item.text }}</p>
          <div class="review-result"><span class="sentiment-pill" :class="item.tone">{{ item.label }}</span><div class="confidence-line"><i><span :style="{ width: item.confidence }" /></i><b>置信度 {{ item.confidence }}</b></div><span v-if="!item.is_certain" class="review-needed"><AppIcon name="alert" /> 建议复核</span></div>
        </div>
      </article>
      <div v-if="!visible.length" class="no-match">没有匹配的评价，换个关键词或筛选条件试试。</div>
    </div>
    <div v-if="results.length" class="list-footer"><span>当前显示 {{ visible.length }} / {{ results.length }} 条</span><span>低于 80% 的结果会进入待复核</span></div>
  </section>
</template>
