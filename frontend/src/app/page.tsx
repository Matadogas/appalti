import Link from 'next/link'

export default function Home() {
  return (
    <div className="max-w-4xl mx-auto py-12">
      <h2 className="text-4xl font-bold mb-6">
        Find Public Construction Opportunities
      </h2>
      <p className="text-lg mb-8 text-gray-700">
        Access aggregated bid opportunities from New York and New Jersey government procurement portals.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Link
          href="/tenders"
          className="block p-6 bg-white rounded-lg shadow hover:shadow-lg transition"
        >
          <h3 className="text-xl font-semibold mb-2">Browse Tenders</h3>
          <p className="text-gray-600">
            Search and filter public works opportunities
          </p>
        </Link>
        <div className="block p-6 bg-gray-100 rounded-lg">
          <h3 className="text-xl font-semibold mb-2">Saved Searches</h3>
          <p className="text-gray-600">
            Coming soon: Save searches and get alerts
          </p>
        </div>
      </div>
    </div>
  )
}
