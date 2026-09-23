// Backend contract: 0 = negative, 1 = positive. Never infer an unknown class.
export function normalizeResults(items, texts) {
  if (!Array.isArray(items) || items.length !== texts.length) throw new Error('返回结果数量与提交数量不一致，请检查接口。')
  return items.map((item, index) => {
    if (!item || item.text !== texts[index]) throw new Error('返回的评价内容或顺序不一致，请检查接口。')
    const labels = new Map([[0, 0], ['0', 0], ['差评', 0], [1, 1], ['1', 1], ['好评', 1]])
    if (!labels.has(item.label)) throw new Error('接口返回未知标签；仅支持 0（差评）和 1（好评）。')
    const labelId = labels.get(item.label)
    if (typeof item.confidence !== 'string' || !/^\d+(?:\.\d+)?%$/.test(item.confidence)) throw new Error('置信度应为百分比字符串，例如 95.00%。')
    const confidenceValue = Number.parseFloat(item.confidence)
    if (confidenceValue < 50 || confidenceValue > 100) throw new Error('二分类所选类别的置信度应在 50%–100% 之间。')
    if (typeof item.is_certain !== 'boolean') throw new Error('接口缺少有效的 is_certain 复核标记。')
    return {
      id: `review-${index}`, text: item.text, labelId,
      label: labelId === 1 ? '好评' : '差评', tone: labelId === 1 ? 'positive' : 'negative',
      confidenceValue, confidence: `${confidenceValue.toFixed(1)}%`,
      // The backend owns the threshold; review is a UI state, never a third class.
      needsReview: !item.is_certain,
    }
  })
}
