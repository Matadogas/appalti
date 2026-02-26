export enum TenderCategory {
  CONSTRUCTION = 'construction',
  ENGINEERING = 'engineering',
  FACILITIES = 'facilities',
  OTHER = 'other',
}

export enum TenderStatus {
  ACTIVE = 'active',
  CLOSED = 'closed',
  AWARDED = 'awarded',
  CANCELLED = 'cancelled',
}

export interface Document {
  name: string
  url: string
  size?: number
}

export interface Contact {
  name?: string
  email?: string
  phone?: string
}

export interface Tender {
  id: string
  source_url: string
  title: string
  description_text?: string
  agency?: string
  state: string
  city?: string
  county?: string
  category: TenderCategory
  status: TenderStatus
  publish_date?: string
  due_date?: string
  budget_amount?: number
  currency: string
  documents: Document[]
  contact?: Contact
  ai_summary?: string
  ai_trade_tags: string[]
  ai_requirements?: Record<string, any>
  confidence?: number
  scraped_at: string
  updated_at: string
}
