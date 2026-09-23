<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import AppIcon from './AppIcon.vue'
import '../welcome.css'

defineProps({ demoMode: Boolean })
const emit = defineEmits(['start', 'example', 'results'])
const scene = ref(null)
const paused = ref(false)
const reduced = ref(false)
const generation = ref(0)
const greetingIndex = ref(0)
const loaded = ref(false)
const failed = ref(false)
const still = computed(() => paused.value || reduced.value)
const greetings = ['你好，我是小听。今天想听听哪些评价？', '把评价交给我，我们一起看看好评与差评。', '复杂的心情，记得结合原文理解。']
const greeting = computed(() => greetings[greetingIndex.value])
let media
let frame
function preference(event) { reduced.value = event.matches; resetTilt() }
function resetTilt() {
  cancelAnimationFrame(frame)
  scene.value?.style.setProperty('--shift-x', '0px')
  scene.value?.style.setProperty('--shift-y', '0px')
}
function tilt(event) {
  if (still.value || event.pointerType !== 'mouse') return
  const rect = scene.value.getBoundingClientRect()
  const x = ((event.clientX - rect.left) / rect.width - .5) * 14
  const y = ((event.clientY - rect.top) / rect.height - .5) * 10
  cancelAnimationFrame(frame)
  frame = requestAnimationFrame(() => {
    scene.value?.style.setProperty('--shift-x', `${x}px`)
    scene.value?.style.setProperty('--shift-y', `${y}px`)
  })
}
function toggleMotion() { paused.value = !paused.value; resetTilt() }
function greet() { greetingIndex.value = (greetingIndex.value + 1) % greetings.length }
onMounted(() => {
  media = matchMedia('(prefers-reduced-motion: reduce)')
  reduced.value = media.matches
  media.addEventListener('change', preference)
})
onBeforeUnmount(() => { media?.removeEventListener('change', preference); cancelAnimationFrame(frame) })
</script>

<template>
  <section id="top" ref="scene" class="welcome-scene" :data-still="still" aria-labelledby="welcome-title" @pointermove="tilt" @pointerleave="resetTilt">
    <div class="scene-grid" aria-hidden="true" />
    <div :key="generation" class="scene-stage">
      <div class="scene-copy">
        <div class="scene-edition scene-entrance"><span class="edition-dot" /> TINGJIAN STUDIO <span class="edition-line" /> 每一句，都听见</div>
        <h1 id="welcome-title" class="scene-entrance">一份外卖，<br />千种<span class="headline-emphasis">心声<svg viewBox="0 0 240 20" preserveAspectRatio="none" aria-hidden="true"><path d="M5 12Q90 1 234 9M14 17Q125 5 219 15" /></svg></span>。</h1>
        <p class="scene-description scene-entrance">好评里的小确幸，差评里的小遗憾。<br />和小听一起，让每条反馈有回响。</p>
        <div class="scene-cta-row scene-entrance">
          <button class="scene-primary" @click="emit('start')"><span>开始倾听</span><span class="cta-arrow"><AppIcon name="arrow" /></span></button>
          <button class="scene-secondary" @click="emit('example')"><span class="example-play">▷</span>试一组评价</button>
        </div>
        <p class="scene-caption scene-entrance"><span>中文情感分析</span><i />好评 / 差评<i />{{ demoMode ? '当前为模拟演示' : '已切换接口模式' }}</p>
        <div class="scene-note scene-entrance"><span class="note-wave" aria-hidden="true"><i /><i /><i /><i /><i /></span><p>认真对待每一句「下次还来」。<small>YOUR FEEDBACK, HEARD.</small></p></div>
      </div>

      <div class="scene-art">
        <div class="art-orbit orbit-outside" aria-hidden="true" /><div class="art-orbit orbit-inside" aria-hidden="true" />
        <span class="art-cross cross-one" aria-hidden="true">+</span><span class="art-cross cross-two" aria-hidden="true">✦</span>
        <div class="character-backdrop" aria-hidden="true"><span>听</span></div>
        <div class="character-parallax">
          <img v-if="!failed" class="mascot-image" :class="{ 'is-loaded': loaded }" src="/images/xiaoting-v2.png" alt="小听：身穿黄黑外套、戴着耳机，手持评价板的原创动漫少女助手" width="1024" height="1536" fetchpriority="high" @load="loaded = true" @error="failed = true" />
          <div v-else class="character-fallback"><AppIcon name="bubble" /><span>每一句，都听见。</span></div>
        </div>
        <div class="floating-review review-positive" aria-hidden="true"><span class="review-mini-icon"><AppIcon name="smile" /></span><div><small>一份被听见的认可</small><b>「热乎乎的，刚刚好！」</b><span>好评 / POSITIVE</span></div></div>
        <div class="floating-review review-negative" aria-hidden="true"><span class="review-mini-icon"><AppIcon name="bubble" /></span><div><small>一次变得更好的机会</small><b>「希望下次再快一点。」</b><span>差评 / NEGATIVE</span></div></div>
        <div class="mascot-tag"><span class="tag-dot" /><b>小听</b><span>你的评价领航员</span></div>
        <button class="mascot-greeting" aria-label="与小听打个招呼" @click="greet"><AppIcon name="spark" /><span aria-live="polite">{{ greeting }}</span></button>
      </div>
    </div>

    <div class="scene-bottom">
      <button class="scene-scroll" @click="emit('start')"><span class="scroll-mark" aria-hidden="true"><i /></span><span>向下，听见更多</span></button>
      <div class="scene-tools"><button :disabled="reduced" :aria-pressed="still" @click="toggleMotion">{{ reduced ? '已跟随系统减少动效' : paused ? '开启动效' : '暂停动效' }}</button><span>/</span><button :disabled="still" @click="generation += 1">重播开场</button></div>
    </div>
    <div class="scene-path" aria-label="使用步骤">
      <button @click="emit('start')"><span>01</span><div><b>放入评价</b><small>粘贴文本或导入 TXT</small></div><AppIcon name="upload" /></button>
      <button @click="emit('start')"><span>02</span><div><b>读懂情绪</b><small>查看好差评与置信度</small></div><AppIcon name="spark" /></button>
      <button @click="emit('results')"><span>03</span><div><b>带走洞察</b><small>筛选、复核与导出</small></div><AppIcon name="download" /></button>
    </div>
  </section>
</template>
