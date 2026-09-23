<script setup>
import { ref } from 'vue'
import AppIcon from './AppIcon.vue'

defineProps({ busy: Boolean, error: String, lineCount: Number, demoMode: Boolean })
const model = defineModel({ type: String, default: '' })
const emit = defineEmits(['analyze'])
const fileInput = ref(null)
const examples = [
  { label: '好评示例', value: '包装很仔细，送到的时候还是热的，味道也很好。' },
  { label: '差评示例', value: '配送太慢了，饭都凉了，餐盒还洒得到处都是。' },
  { label: '模糊评价', value: '味道还可以，但是餐具忘记放了。' },
]

async function readFile(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (file && /\.txt$/i.test(file.name)) model.value = await file.text()
}
</script>

<template>
  <article class="app-card analyzer-card">
    <div class="card-title-row">
      <div class="card-icon yellow"><AppIcon name="bubble" /></div>
      <div><h3>放入顾客评价</h3><p>支持单条或批量分析</p></div>
      <span v-if="demoMode" class="demo-tag">演示数据</span>
    </div>
    <label class="review-input">
      <span>评价内容</span>
      <textarea v-model="model" :disabled="busy" placeholder="今天的外卖怎么样？&#10;每行输入一条评价…" maxlength="100000" @keydown.enter="($event.ctrlKey || $event.metaKey) && ($event.preventDefault(), emit('analyze'))" />
      <small><span>每行一条，最多 500 条</span><b>{{ lineCount }} 条</b></small>
    </label>
    <div class="quick-examples">
      <span>快速试用</span>
      <button v-for="example in examples" :key="example.label" type="button" :disabled="busy" @click="model = example.value">{{ example.label }}</button>
    </div>
    <div v-if="error" class="inline-error" role="alert"><AppIcon name="alert" /><span>{{ error }}</span></div>
    <div class="analyzer-actions">
      <input ref="fileInput" class="visually-hidden" type="file" accept=".txt,text/plain" @change="readFile" />
      <button class="upload-button" type="button" :disabled="busy" @click="fileInput.click()"><AppIcon name="upload" /> 导入 TXT</button>
      <button class="analyze-button" type="button" :disabled="busy" @click="emit('analyze')"><span>{{ busy ? '正在读懂评价…' : '开始分析' }}</span><AppIcon name="arrow" /></button>
    </div>
    <p class="shortcut-hint">Ctrl / Command + Enter 快速提交</p>
  </article>
</template>
