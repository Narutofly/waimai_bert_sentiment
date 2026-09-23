<script setup>
import { computed, ref, watch } from 'vue'
import AppIcon from './AppIcon.vue'

const props = defineProps({ results: { type: Array, required: true }, busy: Boolean, demoMode: Boolean })
const search = defineModel('search', { type: String, default: '' })
const emit = defineEmits(['export'])
const activeFilter = defineModel('activeFilter', { default: 'all' })
const sort = ref('default')
const page = ref(1)
const pageSize = 20
const filters = computed(() => [
  { key: 'all', label: '全部', count: props.results.length },
  { key: 'positive', label: '好评', count: props.results.filter((item) => item.tone === 'positive').length },
  { key: 'negative', label: '差评', count: props.results.filter((item) => item.tone === 'negative').length },
])
const visible = computed(() => {
  const keyword = search.value.trim().toLocaleLowerCase()
  let items = props.results.filter((item) => {
    const filterMatch = activeFilter.value === 'all' || activeFilter.value === item.tone || (activeFilter.value === 'review' && item.needsReview)
    return filterMatch && (!keyword || item.text.toLocaleLowerCase().includes(keyword))
  })
  if (sort.value === 'low') items = [...items].sort((a, b) => (a.confidenceValue ?? Infinity) - (b.confidenceValue ?? Infinity))
  if (sort.value === 'high') items = [...items].sort((a, b) => (b.confidenceValue ?? -Infinity) - (a.confidenceValue ?? -Infinity))
  return items
})
const pages = computed(() => Math.max(1, Math.ceil(visible.value.length / pageSize)))
const pageItems = computed(() => visible.value.slice((page.value - 1) * pageSize, page.value * pageSize))
watch([() => props.results, search, activeFilter, sort], () => { page.value = 1 })
function turnPage(step) {
  page.value = Math.max(1, Math.min(pages.value, page.value + step))
  document.getElementById('reviews')?.scrollIntoView({ block: 'start' })
}
</script>

<template>
  <section id="reviews" class="reviews-section">
    <div class="section-heading reviews-heading"><div><span class="section-kicker">02 / REVIEWS</span><h2>每条反馈，都有回响</h2></div><button class="export-button" aria-label="导出全部筛选结果" type="button" :disabled="!visible.length || busy" @click="emit('export', visible)"><AppIcon name="download" /> 导出筛选结果</button></div>
    <p class="results-source">{{ demoMode ? '模拟演示 · 以下标签及置信度用于交互展示' : '模型预测 · 0 差评 / 1 好评' }}<span v-if="busy"> · 正在分析新一批，以下保留上次结果</span></p>
    <div class="review-toolbar">
      <div class="filter-tabs" role="group" aria-label="评价筛选"><button v-for="filter in filters" :key="filter.key" type="button" :class="{ active: activeFilter === filter.key }" :aria-pressed="activeFilter === filter.key" @click="activeFilter = filter.key">{{ filter.label }} <span>{{ filter.count }}</span></button></div>
      <label class="sort-select"><AppIcon name="filter" /><select v-model="sort" aria-label="结果排序"><option value="default">默认排序</option><option value="low">置信度从低到高</option><option value="high">置信度从高到低</option></select></label>
    </div>
    <div class="review-tools"><label><AppIcon name="search" /><input v-model="search" aria-label="搜索结果原文" type="search" placeholder="在评价原文中搜索" /></label><button type="button" :disabled="busy" :aria-pressed="activeFilter === 'review'" @click="activeFilter = activeFilter === 'review' ? 'all' : 'review'"><AppIcon name="alert" />只看低置信度</button></div>
    <div v-if="!results.length && !busy" class="empty-reviews"><span><AppIcon name="bubble" /></span><h3>还没有评价结果</h3><p>在上方放入评论并开始分析，结果会像真实外卖 App 的评价流一样展示。</p></div>
    <TransitionGroup v-else name="review" tag="div" class="review-list">
      <article v-for="item in pageItems" :key="`${item.id}-${item.text}`" class="review-item">
        <div class="avatar" :class="item.tone">{{ item.tone === 'positive' ? '赞' : '评' }}</div>
        <div class="review-body">
          <div class="review-author"><div><strong>评价 {{ String(Number(item.id.split('-')[1]) + 1).padStart(2, '0') }}</strong><span>{{ demoMode ? '模拟演示' : '本次提交' }}</span></div><span class="label-id">LABEL {{ item.labelId }}</span></div>
          <p>{{ item.text }}</p>
          <div class="review-result"><span class="sentiment-pill" :class="item.tone">{{ item.label }}</span><div v-if="item.confidence !== null" class="confidence-line"><i><span :style="{ width: item.confidence }" /></i><b>置信度 {{ item.confidence }}</b></div><span v-else class="confidence-missing">置信度未提供</span><span v-if="item.needsReview" class="review-needed"><AppIcon name="alert" /> 建议人工复核</span></div>
        </div>
      </article>
      <div v-if="!visible.length" key="empty" class="no-match">{{ busy && !results.length ? '正在等待本次分析结果…' : '没有匹配的评价，试试其他筛选条件。' }}</div>
    </TransitionGroup>
    <div v-if="results.length" class="list-footer"><span>匹配 {{ visible.length }} / {{ results.length }} 条 · 本页 {{ pageItems.length }} 条</span><span>低置信度是复核状态，不是第三类标签</span></div>
    <div v-if="pages > 1" class="pagination"><button :disabled="page === 1" @click="turnPage(-1)">上一页</button><span>{{ page }} / {{ pages }}</span><button :disabled="page === pages" @click="turnPage(1)">下一页</button></div>
  </section>
</template>
