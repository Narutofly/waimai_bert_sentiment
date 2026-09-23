<script setup>
import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue'
import AnalyzerCard from './components/AnalyzerCard.vue'
import AppIcon from './components/AppIcon.vue'
import InsightPanel from './components/InsightPanel.vue'
import ModelReport from './components/ModelReport.vue'
import ReviewFeed from './components/ReviewFeed.vue'
import WelcomeScene from './components/WelcomeScene.vue'
import './desktop.css'
import { checkConnection, classifyReviews, DEMO_MODE } from './services/sentiment.js'

const seedText = `粥还是热的，包装很用心，下次还会点。
等了一个多小时才送到，饭菜都凉了，汤还洒了一半。
分量很足，鸡腿外酥里嫩，配送也很快。
味道还可以，但是餐具忘记放了。`

const text = ref(seedText)
const results = ref([])
const busy = ref(false)
const error = ref('')
const search = ref('')
const connection = ref(DEMO_MODE ? 'demo' : 'checking')
const elapsed = ref('')
const submittedText = ref('')
const activeFilter = ref('all')
const reviewOnly = ref(false)
const activeSection = ref('top')
const notice = ref('')
let noticeTimer
let frame
const navItems = [
  { id: 'top', label: '首页', icon: 'home' },
  { id: 'analyze', label: '评论分析', icon: 'bubble' },
  { id: 'reviews', label: '评价明细', icon: 'filter' },
  { id: 'model', label: '模型报告', icon: 'brain' },
]
function notify(message) {
  notice.value = message
  clearTimeout(noticeTimer)
  noticeTimer = setTimeout(() => { notice.value = '' }, 4000)
}
function tryExample() {
  if (busy.value) return
  text.value = seedText
  navigate('analyze')
  analyze()
}
function navigate(id) {
  activeSection.value = id
  document.getElementById(id)?.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start' })
}
function filterResults(filter) {
  search.value = ''
  activeFilter.value = filter === 'review' ? 'all' : filter
  reviewOnly.value = filter === 'review'
  navigate('reviews')
}
function updateSection() {
  cancelAnimationFrame(frame)
  frame = requestAnimationFrame(() => {
    const sections = navItems.filter((item) => document.getElementById(item.id)?.getBoundingClientRect().top <= 150)
    activeSection.value = sections.at(-1)?.id || 'top'
  })
}
watch(text, () => { error.value = '' })

const lines = computed(() => text.value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean))
const draftChanged = computed(() => results.value.length > 0 && lines.value.join('\n') !== submittedText.value)
const positiveCount = computed(() => results.value.filter((item) => item.tone === 'positive').length)
const negativeCount = computed(() => results.value.filter((item) => item.tone === 'negative').length)
const reviewCount = computed(() => results.value.filter((item) => item.needsReview).length)
const scored = computed(() => results.value.filter((item) => item.confidenceValue !== null))
const averageConfidence = computed(() => scored.value.length
  ? scored.value.reduce((sum, item) => sum + item.confidenceValue, 0) / scored.value.length
  : null)
const positiveRate = computed(() => results.value.length ? positiveCount.value / results.value.length * 100 : 0)
const summary = computed(() => ({
  total: results.value.length,
  positive: positiveCount.value,
  negative: negativeCount.value,
  review: reviewCount.value,
  average: averageConfidence.value,
  positiveRate: positiveRate.value,
  scored: scored.value.length,
}))
const buckets = computed(() => {
  const ranges = [
    { label: '50–60', min: 50, max: 60, count: 0 },
    { label: '60–70', min: 60, max: 70, count: 0 },
    { label: '70–80', min: 70, max: 80, count: 0 },
    { label: '80–90', min: 80, max: 90, count: 0 },
    { label: '90–100', min: 90, max: 101, count: 0 },
  ]
  results.value.forEach((item) => {
    const bucket = ranges.find((range) => item.confidenceValue >= range.min && item.confidenceValue < range.max)
    if (bucket) bucket.count += 1
  })
  return ranges
})

async function analyze(scroll = true) {
  if (busy.value) return
  error.value = ''
  if (!lines.value.length) {
    error.value = '先放入一条评价，再开始分析。'
    return
  }
  if (lines.value.length > 500) {
    error.value = `当前有 ${lines.value.length} 条评价，每次最多分析 500 条。`
    return
  }
  busy.value = true
  const started = performance.now()
  try {
    results.value = await classifyReviews(lines.value)
    submittedText.value = lines.value.join('\n')
    activeFilter.value = 'all'
    reviewOnly.value = false
    search.value = ''
    elapsed.value = ((performance.now() - started) / 1000).toFixed(1)
    if (!DEMO_MODE) connection.value = 'online'
    if (scroll) notify(`${DEMO_MODE ? '演示' : ''}分析完成，共 ${results.value.length} 条评价`)
  } catch (cause) {
    error.value = cause.message || '分析失败，请稍后重试。'
  } finally {
    busy.value = false
  }
}

function exportCsv(items = results.value) {
  if (!items.length) return
  const escapeCell = (value) => { const cell = String(value); return `"${(/^[\s\uFEFF]*[=+@-]/.test(cell) ? `'${cell}` : cell).replace(/"/g, '""')}"` }
  const rows = [
    ['评价内容', '标签编号', '情感判断', '置信度', '建议复核', '来源'],
    ...items.map((item) => [item.text, item.labelId, item.label, item.confidence ?? '未提供', item.confidence === null ? '无法判断' : item.needsReview ? '是' : '否', DEMO_MODE ? '模拟演示' : '模型接口']),
  ]
  const csv = '\uFEFF' + rows.map((row) => row.map(escapeCell).join(',')).join('\r\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  const link = document.createElement('a')
  link.href = url
  link.download = `听见外卖-评价分析-${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
  notify(`已导出 ${items.length} 条评价`)
}

onMounted(async () => {
  window.addEventListener('scroll', updateSection, { passive: true })
  if (DEMO_MODE) {
    await analyze(false)
    return
  }
  connection.value = await checkConnection() ? 'online' : 'offline'
})
onBeforeUnmount(() => {
  window.removeEventListener('scroll', updateSection)
  cancelAnimationFrame(frame)
  clearTimeout(noticeTimer)
})
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="header-inner">
        <a class="brand" href="#top" aria-label="听见外卖首页">
          <span class="brand-mark"><AppIcon name="bubble" /></span>
          <span><b>听见</b><small>外卖评论洞察</small></span>
        </a>
        <nav class="desktop-nav" aria-label="页面导航">
          <a v-for="item in navItems.slice(1)" :key="item.id" :href="`#${item.id}`" :class="{ active: activeSection === item.id }" :aria-current="activeSection === item.id ? 'location' : undefined" @click.prevent="navigate(item.id)">{{ item.label }}</a>
        </nav>
        <div class="service-state" :data-state="connection">
          <i />
          <span>{{ connection === 'demo' ? '前端演示模式' : connection === 'online' ? '模型已连接' : connection === 'checking' ? '正在连接' : '模型未连接' }}</span>
        </div>
      </div>
    </header>

    <WelcomeScene :demo-mode="DEMO_MODE" @start="navigate('analyze')" @example="tryExample" @results="navigate('reviews')" />

    <main>
      <section id="analyze" class="workspace-section">
        <div class="section-heading">
          <div><span class="section-kicker">01 / ANALYZE</span><h2>评论分析</h2></div>
          <p>每行一条评价，也可以直接导入 UTF-8 TXT 文件。</p>
        </div>
        <div class="workspace-grid">
          <AnalyzerCard v-model="text" :busy="busy" :error="error" :line-count="lines.length" :demo-mode="DEMO_MODE" @analyze="analyze" />
          <InsightPanel id="insights" :summary="summary" :buckets="buckets" :busy="busy" :elapsed="elapsed" :demo-mode="DEMO_MODE" @filter="filterResults" />
        </div>
        <div v-if="draftChanged && !busy" class="draft-reminder" role="status"><AppIcon name="info" /><span>输入已修改。看板和评价列表仍显示上一次分析结果。</span><button @click="analyze()">重新分析 <AppIcon name="arrow" /></button></div>
      </section>

      <ReviewFeed v-model:search="search" v-model:active-filter="activeFilter" v-model:review-only="reviewOnly" :results="results" :busy="busy" :demo-mode="DEMO_MODE" @export="exportCsv" />

      <ModelReport />
    </main>

    <footer>
      <div><b>听见外卖</b><span>让每条评价都能变成经营线索</span></div>
      <p>课程项目原型 · 模型判断仅供分析参考</p>
    </footer>

    <nav class="mobile-nav" aria-label="移动端导航">
      <a v-for="item in navItems" :key="item.id" :href="`#${item.id}`" :class="{ active: activeSection === item.id }" :aria-current="activeSection === item.id ? 'location' : undefined" @click.prevent="navigate(item.id)"><AppIcon :name="item.icon" /><span>{{ item.label }}</span></a>
    </nav>
    <div class="notice-region" role="status" aria-live="polite"><Transition name="toast"><div v-if="notice" class="notice-toast"><AppIcon name="bubble" />{{ notice }}</div></Transition></div>
  </div>
</template>
