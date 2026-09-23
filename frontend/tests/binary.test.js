import test from 'node:test'
import assert from 'node:assert/strict'
import { normalizeResults } from '../src/services/binary.js'

const item = (label, overrides = {}) => ({ text: '评价', label, confidence: '95.00%', is_certain: true, ...overrides })
test('numeric and Chinese labels preserve the agreed binary mapping', () => {
  for (const label of [0, '0', '差评', 1, '1', '好评']) {
    const [result] = normalizeResults([item(label)], ['评价'])
    assert.equal(result.labelId, [0, '0', '差评'].includes(label) ? 0 : 1)
    assert.equal(result.label, result.labelId ? '好评' : '差评')
    assert.equal(result.confidenceValue, 95)
  }
})
test('review follows backend certainty without inventing a third class', () => {
  const [result] = normalizeResults([item(1, { confidence: '79.50%', is_certain: false })], ['评价'])
  assert.equal(result.label, '好评')
  assert.equal(result.needsReview, true)
  assert.equal(normalizeResults([item(0, { is_certain: false })], ['评价'])[0].needsReview, true)
})
test('unknown labels and missing probabilities must not render invented results', () => {
  for (const bad of [item(2), item(true), item('中性'), item(0, { confidence: undefined }), item(0, { confidence: 0.95 }), item(0, { confidence: '101%' }), item(0, { confidence: '49%' }), item(0, { is_certain: undefined })]) {
    assert.throws(() => normalizeResults([bad], ['评价']))
  }
})
test('batch alignment is validated before updating the dashboard', () => {
  assert.throws(() => normalizeResults([], ['评价']))
  assert.throws(() => normalizeResults([item(0, { text: '别的内容' })], ['评价']))
  assert.throws(() => normalizeResults(null, ['评价']))
})
