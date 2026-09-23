<script setup>
import { computed, ref, watch } from 'vue'
import AppIcon from './AppIcon.vue'

const props = defineProps({ results: { type: Array, required: true } })
const selectedKey = ref('delivery')
const definitions = [
  { key: 'delivery', label: '配送时效', icon: 'truck', color: '#4f8ef7', words: ['配送', '骑手', '送到', '等了', '慢', '准时', '很快', '凉了'] },
  { key: 'taste', label: '餐品口味', icon: 'bowl', color: '#ef824f', words: ['味道', '好吃', '难吃', '咸', '辣', '油', '香', '口感', '外酥里嫩'] },
  { key: 'package', label: '包装完整', icon: 'box', color: '#8a68d8', words: ['包装', '餐盒', '洒', '漏', '袋子', '汤'] },
  { key: 'value', label: '分量价格', icon: 'wallet', color: '#23a278', words: ['分量', '份量', '足', '少', '贵', '价格', '划算'] },
  { key: 'service', label: '服务细节', icon: 'service', color: '#d9a400', words: ['餐具', '备注', '没放', '忘记', '商家', '态度', '服务'] },
]

const topics = computed(() => definitions.map((definition) => {
  const matched = props.results.filter((item) => definition.words.some((word) => item.text.includes(word)))
  return {
    ...definition,
    count: matched.length,
    negative: matched.filter((item) => item.tone === 'negative').length,
    reviews: matched,
  }
}).sort((a, b) => b.count - a.count || definitions.findIndex((item) => item.key === a.key) - definitions.findIndex((item) => item.key === b.key)))
const maxCount = computed(() => Math.max(1, ...topics.value.map((topic) => topic.count)))
const selected = computed(() => topics.value.find((topic) => topic.key === selectedKey.value) || topics.value[0])
const coveredCount = computed(() => props.results.filter((item) => definitions.some((definition) => definition.words.some((word) => item.text.includes(word)))).length)

watch(topics, (value) => {
  if (!value.some((topic) => topic.key === selectedKey.value && topic.count)) selectedKey.value = value.find((topic) => topic.count)?.key || 'delivery'
}, { immediate: true })
</script>

<template>
  <section id="topics" class="topics-section">
    <div class="section-heading">
      <div><span class="section-kicker">02 / TOPICS</span><h2>顾客都在说什么</h2></div>
      <p>基于评价关键词的前端聚合，用于辅助浏览，不代表 BERT 分类结果。</p>
    </div>
    <div class="topics-layout">
      <div class="topic-overview app-card">
        <div class="topic-overview-head">
          <div><span>主题覆盖</span><strong>{{ coveredCount }} / {{ results.length }}</strong></div>
          <span class="rule-badge">关键词聚合</span>
        </div>
        <div class="topic-bars">
          <button v-for="topic in topics" :key="topic.key" type="button" :class="{ active: selected?.key === topic.key }" @click="selectedKey = topic.key">
            <span class="topic-icon" :style="{ '--topic-color': topic.color }"><AppIcon :name="topic.icon" /></span>
            <span class="topic-name"><b>{{ topic.label }}</b><small>{{ topic.negative }} 条负向</small></span>
            <span class="topic-track"><i :style="{ width: `${topic.count / maxCount * 100}%`, background: topic.color }" /></span>
            <strong>{{ topic.count }}</strong>
          </button>
        </div>
      </div>
      <div class="topic-detail app-card">
        <div class="topic-detail-head">
          <span class="topic-icon large" :style="{ '--topic-color': selected?.color }"><AppIcon :name="selected?.icon || 'bubble'" /></span>
          <div><span>当前主题</span><h3>{{ selected?.label }}</h3></div>
          <strong>{{ selected?.count || 0 }} 次提及</strong>
        </div>
        <div v-if="selected?.reviews.length" class="topic-quotes">
          <article v-for="(review, index) in selected.reviews.slice(0, 3)" :key="`${review.text}-${index}`">
            <span class="quote-tone" :class="review.tone">{{ review.label }}</span>
            <p>{{ review.text }}</p>
            <small>置信度 {{ review.confidence }}</small>
          </article>
        </div>
        <div v-else class="topic-empty"><AppIcon name="bubble" /><p>本次评价暂未提及该主题</p><span>提交更多评价后会自动汇总。</span></div>
      </div>
    </div>
  </section>
</template>
