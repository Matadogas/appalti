'use client'

import { TenderCategory, TenderStatus } from '@/types/tender'

interface TenderFiltersProps {
  state?: string
  category?: TenderCategory
  status?: TenderStatus
  onStateChange: (state: string) => void
  onCategoryChange: (category: TenderCategory | undefined) => void
  onStatusChange: (status: TenderStatus | undefined) => void
}

export function TenderFilters({
  state,
  category,
  status,
  onStateChange,
  onCategoryChange,
  onStatusChange,
}: TenderFiltersProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h3 className="text-lg font-semibold mb-4">Filters</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* State Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            State
          </label>
          <select
            value={state || ''}
            onChange={(e) => onStateChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All States</option>
            <option value="NY">New York</option>
            <option value="NJ">New Jersey</option>
          </select>
        </div>

        {/* Category Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Category
          </label>
          <select
            value={category || ''}
            onChange={(e) =>
              onCategoryChange(
                e.target.value ? (e.target.value as TenderCategory) : undefined
              )
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Categories</option>
            <option value={TenderCategory.CONSTRUCTION}>Construction</option>
            <option value={TenderCategory.ENGINEERING}>Engineering</option>
            <option value={TenderCategory.FACILITIES}>Facilities</option>
            <option value={TenderCategory.OTHER}>Other</option>
          </select>
        </div>

        {/* Status Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Status
          </label>
          <select
            value={status || ''}
            onChange={(e) =>
              onStatusChange(
                e.target.value ? (e.target.value as TenderStatus) : undefined
              )
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value={TenderStatus.ACTIVE}>Active</option>
            <option value={TenderStatus.CLOSED}>Closed</option>
            <option value={TenderStatus.AWARDED}>Awarded</option>
            <option value={TenderStatus.CANCELLED}>Cancelled</option>
          </select>
        </div>
      </div>
    </div>
  )
}
