<script setup>
import { computed, onMounted, ref } from 'vue'
import AnalyzerCard from './components/AnalyzerCard.vue'
import AppIcon from './components/AppIcon.vue'
import InsightPanel from './components/InsightPanel.vue'
import ModelReport from './components/ModelReport.vue'
import ReviewFeed from './components/ReviewFeed.vue'
import TopicPanel from './components/TopicPanel.vue'
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

const lines = computed(() => text.value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean))
const positiveCount = computed(() => results.value.filter((item) => item.tone === 'positive').length)
const negativeCount = computed(() => results.value.filter((item) => item.tone === 'negative').length)
const reviewCount = computed(() => results.value.filter((item) => !item.is_certain).length)
const averageConfidence = computed(() => results.value.length
  ? results.value.reduce((sum, item) => sum + item.confidenceValue, 0) / results.value.length
  : 0)
const positiveRate = computed(() => results.value.length ? positiveCount.value / results.value.length * 100 : 0)
const summary = computed(() => ({
  total: results.value.length,
  positive: positiveCount.value,
  negative: negativeCount.value,
  review: reviewCount.value,
  average: averageConfidence.value,
  positiveRate: positiveRate.value,
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

async function analyze() {
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
    elapsed.value = ((performance.now() - started) / 1000).toFixed(1)
    window.setTimeout(() => document.querySelector('#insights')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 80)
  } catch (cause) {
    error.value = cause.message || '分析失败，请稍后重试。'
    connection.value = 'offline'
  } finally {
    busy.value = false
  }
}

function exportCsv(items = results.value) {
  if (!items.length) return
  const escapeCell = (value) => `"${String(value).replace(/"/g, '""')}"`
  const rows = [
    ['评价内容', '情感判断', '置信度', '建议复核'],
    ...items.map((item) => [item.text, item.label, item.confidence, item.is_certain ? '否' : '是']),
  ]
  const csv = '\uFEFF' + rows.map((row) => row.map(escapeCell).join(',')).join('\r\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  const link = document.createElement('a')
  link.href = url
  link.download = `听见外卖-评价分析-${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  if (DEMO_MODE) {
    await analyze()
    return
  }
  connection.value = await checkConnection() ? 'online' : 'offline'
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
          <a class="active" href="#analyze">评论分析</a>
          <a href="#topics">主题洞察</a>
          <a href="#reviews">评价明细</a>
          <a href="#model">模型报告</a>
        </nav>
        <div class="service-state" :data-state="connection">
          <i />
          <span>{{ connection === 'demo' ? '前端演示模式' : connection === 'online' ? '模型已连接' : connection === 'checking' ? '正在连接' : '模型未连接' }}</span>
        </div>
      </div>
    </header>

    <section id="top" class="hero">
      <div class="hero-inner">
        <div class="location-row">
          <span><AppIcon name="pin" />校园商圈 · 示例门店</span>
          <button type="button">切换门店 <AppIcon name="chevron" /></button>
        </div>
        <div class="hero-copy">
          <div>
            <p class="eyebrow"><span>AI</span> 评论经营助手</p>
            <h1>听懂顾客的每一句反馈</h1>
            <p>批量识别外卖评价情绪，快速找到值得关注的差评和模糊反馈。</p>
          </div>
          <div class="hero-orbit" aria-hidden="true">
            <span class="orbit-card good">好评 <b>{{ summary.positive }}</b></span>
            <span class="orbit-card risk">待复核 <b>{{ summary.review }}</b></span>
            <span class="orbit-center"><AppIcon name="spark" /></span>
          </div>
        </div>
        <label class="hero-search">
          <AppIcon name="search" />
          <input v-model="search" type="search" placeholder="搜索本次评价中的关键词" />
          <span>{{ results.length }} 条评价</span>
        </label>
      </div>
    </section>

    <main>
      <section id="analyze" class="workspace-section">
        <div class="section-heading">
          <div><span class="section-kicker">01 / ANALYZE</span><h2>评论分析</h2></div>
          <p>每行一条评价，也可以直接导入 UTF-8 TXT 文件。</p>
        </div>
        <div class="workspace-grid">
          <AnalyzerCard v-model="text" :busy="busy" :error="error" :line-count="lines.length" :demo-mode="DEMO_MODE" @analyze="analyze" />
          <InsightPanel id="insights" :summary="summary" :buckets="buckets" :busy="busy" :elapsed="elapsed" />
        </div>
      </section>

      <TopicPanel :results="results" />

      <ReviewFeed v-model:search="search" :results="results" :busy="busy" @export="exportCsv" />

      <ModelReport />
    </main>

    <footer>
      <div><b>听见外卖</b><span>让每条评价都能变成经营线索</span></div>
      <p>课程项目原型 · 模型判断仅供分析参考</p>
    </footer>

    <nav class="mobile-nav" aria-label="移动端导航">
      <a href="#top"><AppIcon name="home" /><span>首页</span></a>
      <a class="active" href="#analyze"><AppIcon name="bubble" /><span>分析</span></a>
      <a href="#topics"><AppIcon name="chart" /><span>洞察</span></a>
      <a href="#model"><AppIcon name="store" /><span>模型</span></a>
    </nav>
  </div>
</template>
