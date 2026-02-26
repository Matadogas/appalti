import { Tender } from '@/types/tender'
import { formatDistanceToNow } from 'date-fns'
import Link from 'next/link'

interface TenderCardProps {
  tender: Tender
}

export function TenderCard({ tender }: TenderCardProps) {
  const dueDateText = tender.due_date
    ? formatDistanceToNow(new Date(tender.due_date), { addSuffix: true })
    : null

  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition">
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-xl font-semibold text-gray-900 flex-1">
          <Link href={`/tenders/${tender.id}`} className="hover:text-blue-600">
            {tender.title}
          </Link>
        </h3>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
          tender.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
        }`}>
          {tender.status}
        </span>
      </div>

      <div className="flex gap-2 mb-3">
        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded">
          {tender.state}
        </span>
        <span className="px-2 py-1 bg-purple-100 text-purple-800 text-sm rounded">
          {tender.category}
        </span>
      </div>

      {tender.agency && (
        <p className="text-sm text-gray-600 mb-2">
          <strong>Agency:</strong> {tender.agency}
        </p>
      )}

      {tender.city && (
        <p className="text-sm text-gray-600 mb-2">
          <strong>Location:</strong> {tender.city}
          {tender.county && `, ${tender.county} County`}
        </p>
      )}

      {tender.ai_summary && (
        <p className="text-gray-700 mb-3">{tender.ai_summary}</p>
      )}

      {tender.ai_trade_tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {tender.ai_trade_tags.map((tag) => (
            <span
              key={tag}
              className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      <div className="flex justify-between items-center text-sm text-gray-500 mt-4">
        {dueDateText && (
          <span className="font-medium text-red-600">Due {dueDateText}</span>
        )}
        <a
          href={tender.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline"
        >
          View Original &rarr;
        </a>
      </div>
    </div>
  )
}
