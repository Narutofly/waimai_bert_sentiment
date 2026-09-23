import test from 'node:test'
import assert from 'node:assert/strict'
import { filterReviews, highlightText } from '../src/services/reviewView.js'
const items = [
  { id: 'a', text: '配送快', tone: 'positive', confidenceValue: 65, needsReview: true },
  { id: 'b', text: '配送慢', tone: 'negative', confidenceValue: 75, needsReview: true },
  { id: 'c', text: '包装漏', tone: 'negative', confidenceValue: 95, needsReview: false },
]
test('sentiment, review state and search compose without dropping filters', () => {
  assert.deepEqual(filterReviews(items, { sentiment: 'negative', reviewOnly: true, search: '配送' }).map(x => x.id), ['b'])
  assert.equal(filterReviews(items, { sentiment: 'positive', reviewOnly: true, search: '包装' }).length, 0)
})
test('sorting does not change the original ordering or IDs', () => {
  assert.deepEqual(filterReviews(items, { sort: 'high' }).map(x => x.id), ['c', 'b', 'a'])
  assert.deepEqual(items.map(x => x.id), ['a', 'b', 'c'])
})
test('highlight treats markup and regex-like user text literally', () => {
  const original = '<script>配送.*配送.*</script>'
  const parts = highlightText(original, '配送.*')
  assert.equal(parts.map(x => x.text).join(''), original)
  assert.deepEqual(parts.filter(x => x.match).map(x => x.text), ['配送.*', '配送.*'])
  assert.equal(highlightText('BERT bert', 'bert').filter(x => x.match).length, 2)
  assert.deepEqual(highlightText('原文', '  '), [{ text: '原文', match: false }])
})
