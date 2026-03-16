export async function loadAllPaginatedResults(request, initialParams = {}, maxPages = 50) {
  const items = []
  const seenIds = new Set()
  let page = 1

  while (page <= maxPages) {
    const response = await request({ ...initialParams, page })
    const data = response.data || {}
    const rows = data.results || data || []

    rows.forEach((row) => {
      const key = row?.id ?? `${row?.descricao || row?.nome || ''}-${items.length}`
      if (!seenIds.has(key)) {
        seenIds.add(key)
        items.push(row)
      }
    })

    if (!data.next) {
      break
    }

    page += 1
  }

  return items
}