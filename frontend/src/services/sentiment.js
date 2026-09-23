export const DEMO_MODE = import.meta.env.VITE_USE_MOCK !== 'false'
const API_BASE = (import.meta.env.VITE_API_BASE || '/api/v1').replace(/\/+$/, '')
const positiveWords = ['好吃', '很好', '满意', '很快', '用心', '热的', '新鲜', '足', '香', '推荐', '不错', '喜欢', '准时', '干净']
const negativeWords = ['难吃', '太慢', '凉了', '洒', '少了', '忘记', '没放', '糟糕', '失望', '异物', '不新鲜', '等了', '油腻', '贵']

function decorate(item) {
  const confidenceValue = Number.parseFloat(item.confidence)
  const positive = /^(好评|正面|正向|积极|positive)$/i.test(item.label)
  return { ...item, confidenceValue: Number.isFinite(confidenceValue) ? confidenceValue : 0, tone: positive ? 'positive' : 'negative' }
}
function mockResult(text) {
  const positiveScore = positiveWords.reduce((score, word) => score + (text.includes(word) ? 1 : 0), 0)
  const negativeScore = negativeWords.reduce((score, word) => score + (text.includes(word) ? 1 : 0), 0)
  const hash = [...text].reduce((value, char) => (value * 31 + char.charCodeAt(0)) % 997, 17)
  const positive = positiveScore === negativeScore ? hash % 2 === 0 : positiveScore > negativeScore
  const confidenceValue = Math.min(98.6, 58 + Math.abs(positiveScore - negativeScore) * 12 + (hash % 80) / 10)
  return decorate({ text, label: positive ? '好评' : '差评', confidence: `${confidenceValue.toFixed(1)}%`, is_certain: confidenceValue >= 80 })
}
export async function classifyReviews(texts) {
  if (DEMO_MODE) {
    await new Promise((resolve) => window.setTimeout(resolve, 520))
    return texts.map(mockResult)
  }
  const response = await fetch(`${API_BASE}/classify`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: texts.length === 1 ? texts[0] : texts }) })
  const payload = await response.json().catch(() => null)
  if (!response.ok || payload?.code !== 200 || !Array.isArray(payload.results)) throw new Error(payload?.message || `分析服务暂不可用（${response.status}）`)
  return payload.results.map(decorate)
}
export async function checkConnection() {
  try {
    const response = await fetch(`${API_BASE}/`, { signal: AbortSignal.timeout(6000) })
    const payload = await response.json()
    return response.ok && payload?.code === 200
  } catch { return false }
}
