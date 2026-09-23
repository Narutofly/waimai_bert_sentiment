<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import AppIcon from './AppIcon.vue'

const item = defineModel({ default: null })
const props = defineProps({ items: { type: Array, required: true }, demoMode: Boolean })
const dialog = ref(null)
const copyState = ref('')
const copying = ref(false)
const original = ref(null)
const previous = computed(() => props.items.findIndex((entry) => entry.id === item.value?.id))
let savedOverflow = ''
let locked = false
let returnFocus = null
let version = 0

function unlock() {
  if (locked) document.body.style.overflow = savedOverflow
  locked = false
}
function close() {
  version += 1
  dialog.value?.close()
  item.value = null
  copyState.value = ''
  unlock()
  if (returnFocus?.isConnected) returnFocus.focus({ preventScroll: true })
}
function backdrop(event) {
  if (event.target !== dialog.value) return
  const bounds = dialog.value.getBoundingClientRect()
  if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) close()
}
function move(direction) {
  const candidate = props.items[previous.value + direction]
  if (candidate) item.value = candidate
}
async function copyText() {
  if (!item.value || copying.value) return
  const current = version
  const text = item.value.text
  copying.value = true
  try {
    await navigator.clipboard.writeText(text)
    if (current === version) copyState.value = '原文已复制'
  } catch {
    if (current === version) {
      copyState.value = '无法自动复制，已选中原文，请按 Ctrl / ⌘ + C'
      const range = document.createRange()
      range.selectNodeContents(original.value)
      const selection = window.getSelection()
      selection.removeAllRanges()
      selection.addRange(range)
    }
  } finally { copying.value = false }
}

watch(item, async (value, oldValue) => {
  version += 1
  copyState.value = ''
  if (!value) { dialog.value?.close(); unlock(); return }
  if (!oldValue) returnFocus = document.activeElement
  await nextTick()
  if (!item.value) return
  if (!dialog.value.open) {
    savedOverflow = document.body.style.overflow
    locked = true
    document.body.style.overflow = 'hidden'
    dialog.value.showModal()
  }
  dialog.value.querySelector('.detail-scroll')?.scrollTo(0, 0)
})
onBeforeUnmount(unlock)
</script>

<template>
  <dialog ref="dialog" class="detail-dialog" aria-labelledby="detail-title" @cancel.prevent="close" @close="close" @click="backdrop">
    <template v-if="item">
      <header class="detail-header">
        <div><span class="section-kicker">REVIEW / {{ String(Number(item.id.split('-')[1]) + 1).padStart(2, '0') }}</span><h2 id="detail-title">评价详情</h2></div>
        <button class="detail-close" aria-label="关闭评价详情" autofocus @click="close"><AppIcon name="close" /></button>
      </header>
      <div class="detail-scroll">
        <div class="detail-verdict" :class="item.tone">
          <span class="detail-face"><AppIcon :name="item.tone === 'positive' ? 'smile' : 'frown'" /></span>
          <div><p>{{ demoMode ? '模拟演示结果' : '模型预测结果' }}</p><strong>{{ item.label }}</strong><small>类别 {{ item.labelId }} · {{ item.labelId === 1 ? '正向反馈' : '负向反馈' }}</small></div>
          <div class="detail-score"><strong>{{ item.confidence }}</strong><span>预测置信度</span></div>
        </div>
        <div class="detail-confidence" :class="item.tone"><i :style="{ width: item.confidence }" /></div>
        <p class="detail-status" :class="{ uncertain: item.needsReview }"><AppIcon :name="item.needsReview ? 'alert' : 'check'" />{{ item.needsReview ? '低置信度，建议结合原文人工复核' : '高置信度预测，仍需结合语境理解' }}</p>

        <div class="original-heading"><h3>顾客说了什么</h3><span>{{ item.text.length }} 字符</span></div>
        <blockquote ref="original" class="detail-original">{{ item.text }}</blockquote>

        <div class="detail-explanation"><AppIcon name="info" /><p>置信度表示模型对本次分类的把握程度，不代表顾客满意度，也不是模型在测试集上的准确率。</p></div>
        <details class="detail-method"><summary>这条结果如何阅读？</summary><p>0 为差评，1 为好评。模型对整条评价进行一次分类；一句话中同时出现表扬与抱怨时，结果也只有一个标签。</p><p>“建议复核”是单独的状态，不会把好评或差评变成第三类。{{ demoMode ? '当前结果来自前端演示规则，请勿用于实际经营判断。' : '复核标记遵循后端返回的判断。' }}</p></details>
      </div>
      <footer class="detail-footer">
        <p class="copy-feedback" role="status">{{ copyState }}</p>
        <div><button class="copy-original" :disabled="copying" @click="copyText"><AppIcon name="copy" />{{ copying ? '复制中…' : '复制原文' }}</button><nav class="detail-pager" aria-label="切换评价"><button :disabled="previous <= 0" aria-label="上一条评价" @click="move(-1)"><AppIcon name="chevron" /></button><span>{{ previous + 1 }} / {{ items.length }}</span><button :disabled="previous >= items.length - 1" aria-label="下一条评价" @click="move(1)"><AppIcon name="chevron" /></button></nav></div>
      </footer>
    </template>
  </dialog>
</template>
