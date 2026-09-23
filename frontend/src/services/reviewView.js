export function filterReviews(results, { sentiment = 'all', reviewOnly = false, search = '', sort = 'default' } = {}) {
  const keyword = search.trim().toLocaleLowerCase()
  const items = results.filter((item) => (sentiment === 'all' || item.tone === sentiment)
    && (!reviewOnly || item.needsReview)
    && (!keyword || item.text.toLocaleLowerCase().includes(keyword)))
  if (sort === 'low') items.sort((a, b) => a.confidenceValue - b.confidenceValue)
  if (sort === 'high') items.sort((a, b) => b.confidenceValue - a.confidenceValue)
  return items
}

// Return text pieces, never HTML. A search term such as "<script>" remains plain text.
export function highlightText(text, search) {
  const query = search.trim().toLocaleLowerCase()
  if (!query) return [{ text, match: false }]
  const lower = text.toLocaleLowerCase()
  const pieces = []
  let offset = 0
  let found
  while ((found = lower.indexOf(query, offset)) !== -1) {
    if (found > offset) pieces.push({ text: text.slice(offset, found), match: false })
    pieces.push({ text: text.slice(found, found + query.length), match: true })
    offset = found + query.length
  }
  if (offset < text.length) pieces.push({ text: text.slice(offset), match: false })
  return pieces
}
