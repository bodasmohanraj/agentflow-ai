
import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import { apiFetch, getToken, logout } from '../../src/lib/api'

interface DashboardStats {
  total_clients: number
  active_projects: number
  completed_projects: number
  pending_approvals: number
  running_agents: number
  completed_tasks: number
}

export default function DashboardPage() {
  const router = useRouter()

  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function loadDashboard() {
      if (!getToken()) {
        router.replace('/login')
        return
      }

      try {
        const data = await apiFetch<DashboardStats>(
          '/agency/dashboard/stats'
        )

        if (!cancelled) {
          setStats(data)
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : 'Unable to load dashboard'
          )
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadDashboard()

    return () => {
      cancelled = true
    }
  }, [router])

  const cards = stats
    ? [
        { label: 'Total Clients', value: stats.total_clients },
        { label: 'Active Projects', value: stats.active_projects },
        { label: 'Completed Projects', value: stats.completed_projects },
        { label: 'Pending Approvals', value: stats.pending_approvals },
        { label: 'Running Agents', value: stats.running_agents },
        { label: 'Completed Tasks', value: stats.completed_tasks },
      ]
    : []

  if (loading) {
    return <div className="p-8">Loading your dashboard...</div>
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <p className="mb-4 text-red-600">{error}</p>
        <button
          onClick={logout}
          className="rounded bg-blue-600 px-4 py-2 text-white"
        >
          Return to Login
        </button>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-3xl font-bold">Agency Dashboard</h1>

          <button
            onClick={logout}
            className="rounded-md bg-red-600 px-4 py-2 text-white hover:bg-red-700"
          >
            Logout
          </button>
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {cards.map((card) => (
            <div
              key={card.label}
              className="rounded-lg bg-white p-6 shadow"
            >
              <h3 className="text-sm font-medium text-gray-500">
                {card.label}
              </h3>

              <p className="mt-2 text-2xl font-bold">
                {card.value}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

