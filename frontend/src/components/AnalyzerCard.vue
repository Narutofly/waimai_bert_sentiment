<script setup>
import { ref, watch } from 'vue'
import AppIcon from './AppIcon.vue'

const props = defineProps({ busy: Boolean, error: String, lineCount: Number, demoMode: Boolean })
const model = defineModel({ type: String, default: '' })
const emit = defineEmits(['analyze'])
const fileInput = ref(null)
const fileError = ref('')
const fileName = ref('')
const reading = ref(false)
const dragging = ref(false)
watch(model, () => { fileError.value = '' })
const examples = [
  { label: '好评示例', value: '包装很仔细，送到的时候还是热的，味道也很好。' },
  { label: '差评示例', value: '配送太慢了，饭都凉了，餐盒还洒得到处都是。' },
  { label: '混合表达', value: '味道还可以，但是餐具忘记放了。' },
  { label: '试试一组评价', value: '粥还是热的，包装很用心，下次还会点。\n等了一个多小时才送到，饭菜都凉了。\n分量很足，配送也很快。\n味道还可以，但是餐具忘记放了。' },
]

async function readFile(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  await loadFile(file)
}
async function loadFile(file) {
  if (!file || props.busy || reading.value) return
  fileError.value = ''
  fileName.value = ''
  reading.value = true
  try {
    if (!/\.txt$/i.test(file.name)) throw new Error('请选择 TXT 文件。')
    if (file.size > 2 * 1024 * 1024) throw new Error('文件超过 2 MB，请拆分后导入。')
    let content
    try { content = new TextDecoder('utf-8', { fatal: true }).decode(await file.arrayBuffer()) }
    catch { throw new Error('请将文件保存为 UTF-8 编码后重试。') }
    const lines = content.split(/\r?\n/).filter((line) => line.trim())
    if (!lines.length || lines.length > 500 || content.length > 100000) throw new Error('请导入 1–500 条评价，且总长度不超过 100,000 字符。')
    model.value = content
    fileName.value = file.name
  } catch (cause) { fileError.value = cause.message }
  finally { reading.value = false }
}
function dropFile(event) {
  dragging.value = false
  if (event.dataTransfer.files.length !== 1) { fileError.value = '每次请拖入一个 TXT 文件。'; return }
  loadFile(event.dataTransfer.files[0])
}
</script>

<template>
  <article class="app-card analyzer-card" :class="{ dragging }" @dragover.prevent="dragging = !busy && !reading" @dragleave.prevent="dragging = false" @drop.prevent="dropFile">
    <div class="card-title-row">
      <div class="card-icon yellow"><AppIcon name="bubble" /></div>
      <div><h3>放入顾客评价</h3><p>支持单条或批量分析</p></div>
      <span v-if="demoMode" class="demo-tag">演示数据</span>
    </div>
    <div class="review-input">
      <span><label for="review-text">评价内容</label><button class="clear-input" type="button" :disabled="busy || reading || !model" @click="model = ''; fileName = ''">清空</button></span>
      <textarea id="review-text" v-model="model" aria-label="评价内容" :disabled="busy || reading" placeholder="今天的外卖怎么样？&#10;每行输入一条评价…" maxlength="100000" @input="fileName = ''" @keydown.enter="!reading && ($event.ctrlKey || $event.metaKey) && ($event.preventDefault(), emit('analyze'))" />
      <small><span>每行一条，最多 500 条</span><b>{{ lineCount }} 条</b></small>
    </div>
    <div class="quick-examples">
      <span>快速试用</span>
      <button v-for="example in examples" :key="example.label" type="button" :disabled="busy || reading" @click="model = example.value; fileName = ''">{{ example.label }}</button>
    </div>
    <div v-if="error || fileError" class="inline-error" role="alert"><AppIcon name="alert" /><span>{{ fileError || error }}</span></div>
    <p v-if="fileName" class="file-receipt" role="status"><AppIcon name="box" /> 已导入 {{ fileName }}</p>
    <div class="analyzer-actions">
      <input ref="fileInput" class="visually-hidden" aria-label="选择评价 TXT 文件" :disabled="busy || reading" type="file" accept=".txt,text/plain" @change="readFile" />
      <button class="upload-button" type="button" :disabled="busy || reading" @click="fileInput.click()"><AppIcon name="upload" /> {{ reading ? '读取中…' : '导入 TXT' }}</button>
      <button class="analyze-button" type="button" :disabled="busy || reading" @click="emit('analyze')"><span>{{ busy ? '正在分析…' : '开始分析' }}</span><AppIcon name="arrow" /></button>
    </div>
    <p class="shortcut-hint">拖入 UTF-8 TXT · 最大 2 MB · Ctrl / ⌘ + Enter 提交</p>
  </article>
</template>
