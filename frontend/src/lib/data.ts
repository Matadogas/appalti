import tendersData from '@/data/tenders.json'

export interface Tender {
  id: string
  title: string
  agency: string
  state: string
  city: string
  category: string
  status: string
  dueDate: string | null
  publishDate: string | null
  sourceUrl: string
  source: string
  description: string
  rawRef: Record<string, any>
}

export interface TendersData {
  scrapedAt: string
  totalCount: number
  sourceCounts: Record<string, number>
  tenders: Tender[]
}

const data = tendersData as TendersData

export function getAllTenders(): Tender[] {
  return data.tenders
}

export function getTenderById(id: string): Tender | undefined {
  return data.tenders.find(t => t.id === id)
}

export function getAllTenderIds(): string[] {
  return data.tenders.map(t => t.id)
}

export function getScrapedAt(): string {
  return data.scrapedAt
}

export function getSourceCounts(): Record<string, number> {
  return data.sourceCounts
}

export function getTotalCount(): number {
  return data.totalCount
}

export function getSimilarTenders(tender: Tender, limit = 4): Tender[] {
  return data.tenders
    .filter(t => t.id !== tender.id)
    .filter(t => t.category === tender.category || t.agency === tender.agency || t.source === tender.source)
    .sort((a, b) => {
      // Prioritize same category + same source
      let scoreA = 0, scoreB = 0
      if (a.category === tender.category) scoreA += 2
      if (a.agency === tender.agency) scoreA += 3
      if (a.source === tender.source) scoreA += 1
      if (b.category === tender.category) scoreB += 2
      if (b.agency === tender.agency) scoreB += 3
      if (b.source === tender.source) scoreB += 1
      return scoreB - scoreA
    })
    .slice(0, limit)
}

export function getUpcomingDeadlines(limit = 5): Tender[] {
  const now = new Date().toISOString().split('T')[0]
  return data.tenders
    .filter(t => t.dueDate && t.dueDate >= now)
    .sort((a, b) => (a.dueDate || '').localeCompare(b.dueDate || ''))
    .slice(0, limit)
}

export function getCategoryBreakdown(): { category: string; count: number }[] {
  const counts: Record<string, number> = {}
  data.tenders.forEach(t => {
    counts[t.category] = (counts[t.category] || 0) + 1
  })
  return Object.entries(counts)
    .map(([category, count]) => ({ category, count }))
    .sort((a, b) => b.count - a.count)
}

export function getUniqueAgencies(): string[] {
  return [...new Set(data.tenders.map(t => t.agency))].sort()
}

export function getUniqueSources(): string[] {
  return [...new Set(data.tenders.map(t => t.source))].sort()
}
