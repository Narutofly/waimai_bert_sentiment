<script setup>
import { computed, ref, watch } from 'vue'
import AppIcon from './AppIcon.vue'
import ReviewDetail from './ReviewDetail.vue'
import { filterReviews, highlightText } from '../services/reviewView.js'

const props = defineProps({ results: { type: Array, required: true }, busy: Boolean, demoMode: Boolean })
const search = defineModel('search', { type: String, default: '' })
const emit = defineEmits(['export'])
const activeFilter = defineModel('activeFilter', { default: 'all' })
const reviewOnly = defineModel('reviewOnly', { default: false })
const sort = ref('default')
const page = ref(1)
const pageSize = ref(20)
const selected = ref(null)
const filters = computed(() => [
  { key: 'all', label: '全部', count: props.results.length },
  { key: 'positive', label: '好评', count: props.results.filter((item) => item.tone === 'positive').length },
  { key: 'negative', label: '差评', count: props.results.filter((item) => item.tone === 'negative').length },
])
const visible = computed(() => filterReviews(props.results, { sentiment: activeFilter.value, reviewOnly: reviewOnly.value, search: search.value, sort: sort.value }))
const pages = computed(() => Math.max(1, Math.ceil(visible.value.length / pageSize.value)))
const pageItems = computed(() => visible.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value))
const hasFilters = computed(() => activeFilter.value !== 'all' || reviewOnly.value || search.value.trim())
watch([() => props.results, search, activeFilter, reviewOnly, sort, pageSize], () => { page.value = 1; selected.value = null })
function resetFilters() { activeFilter.value = 'all'; reviewOnly.value = false; search.value = '' }
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
    <div class="review-tools"><label><AppIcon name="search" /><input v-model="search" aria-label="搜索结果原文" type="search" placeholder="在评价原文中搜索" /></label><button type="button" :disabled="busy" :aria-pressed="reviewOnly" @click="reviewOnly = !reviewOnly"><AppIcon name="alert" />只看低置信度</button></div>
    <div v-if="hasFilters" class="active-criteria"><span>当前筛选</span><button v-if="activeFilter !== 'all'" @click="activeFilter = 'all'">{{ activeFilter === 'positive' ? '好评' : '差评' }} <AppIcon name="close" /></button><button v-if="reviewOnly" @click="reviewOnly = false">低置信度 <AppIcon name="close" /></button><button v-if="search.trim()" @click="search = ''">“{{ search.trim() }}” <AppIcon name="close" /></button><button class="reset-criteria" @click="resetFilters">重置筛选</button></div>
    <div v-if="!results.length && !busy" class="empty-reviews"><span><AppIcon name="bubble" /></span><h3>还没有评价结果</h3><p>在上方放入评论并开始分析，结果会像真实外卖 App 的评价流一样展示。</p></div>
    <TransitionGroup v-else name="review" tag="div" class="review-list">
      <article v-for="item in pageItems" :key="`${item.id}-${item.text}`" class="review-item">
        <div class="avatar" :class="item.tone">{{ item.tone === 'positive' ? '赞' : '评' }}</div>
        <div class="review-body">
          <div class="review-author"><div><strong>评价 {{ String(Number(item.id.split('-')[1]) + 1).padStart(2, '0') }}</strong><span>{{ demoMode ? '模拟演示' : '本次提交' }}</span></div><button class="open-detail" :aria-label="`查看评价 ${Number(item.id.split('-')[1]) + 1} 详情`" @click="selected = item">查看详情 <AppIcon name="chevron" /></button></div>
          <p class="review-excerpt"><template v-for="(part, index) in highlightText(item.text, search)" :key="index"><mark v-if="part.match">{{ part.text }}</mark><template v-else>{{ part.text }}</template></template></p>
          <div class="review-result"><span class="sentiment-pill" :class="item.tone">{{ item.label }}</span><div v-if="item.confidence !== null" class="confidence-line"><i><span :style="{ width: item.confidence }" /></i><b>置信度 {{ item.confidence }}</b></div><span v-else class="confidence-missing">置信度未提供</span><span v-if="item.needsReview" class="review-needed"><AppIcon name="alert" /> 建议人工复核</span></div>
        </div>
      </article>
      <div v-if="!visible.length" key="empty" class="no-match"><AppIcon name="search" /><p>{{ busy && !results.length ? '正在等待本次分析结果…' : '没有找到符合这些条件的评价' }}</p><button v-if="hasFilters" @click="resetFilters">清除筛选，查看全部</button></div>
    </TransitionGroup>
    <div v-if="results.length" class="list-footer"><span>匹配 {{ visible.length }} / {{ results.length }} 条 · 本页 {{ pageItems.length }} 条</span><span>低置信度是复核状态，不是第三类标签</span></div>
    <div v-if="results.length" class="pagination"><label>每页 <select v-model.number="pageSize" aria-label="每页条数"><option :value="10">10 条</option><option :value="20">20 条</option><option :value="50">50 条</option></select></label><button :disabled="page === 1" @click="turnPage(-1)">上一页</button><span>{{ page }} / {{ pages }}</span><button :disabled="page === pages" @click="turnPage(1)">下一页</button></div>
    <ReviewDetail v-model="selected" :items="visible" :demo-mode="demoMode" />
  </section>
</template>
