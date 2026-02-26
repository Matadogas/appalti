import axios from 'axios'
import { Tender, TenderCategory, TenderStatus } from '@/types/tender'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface ListTendersParams {
  skip?: number
  limit?: number
  state?: string
  category?: TenderCategory
  status?: TenderStatus
}

export async function listTenders(params?: ListTendersParams): Promise<Tender[]> {
  const response = await api.get('/tenders', { params })
  return response.data
}

export async function getTender(id: string): Promise<Tender> {
  const response = await api.get(`/tenders/${id}`)
  return response.data
}

export async function countTenders(params?: Omit<ListTendersParams, 'skip' | 'limit'>): Promise<number> {
  const response = await api.get('/tenders/count', { params })
  return response.data.count
}
