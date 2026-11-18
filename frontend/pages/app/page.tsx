import { useEffect, useState } from 'react'

export default function DashboardPage() {
  const stats = {
    total_clients: 5,
    active_projects: 3,
    pending_approvals: 2,
    recent_activity: [
      { id: 1, action: 'Research Agent finished competitor audit', time: '10 mins ago' },
      { id: 2, action: 'Content Agent generated social post', time: '25 mins ago' },
    ]
  }

  return (
    <div className="p-8 max-w-7xl mx-auto bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold mb-8">Agency Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="p-6 bg-white shadow rounded-lg">
          <h3 className="text-sm font-medium text-gray-500">Total Clients</h3>
          <p className="text-2xl font-bold">{stats.total_clients}</p>
        </div>
        <div className="p-6 bg-white shadow rounded-lg">
          <h3 className="text-sm font-medium text-gray-500">Active Projects</h3>
          <p className="text-2xl font-bold">{stats.active_projects}</p>
        </div>
        <div className="p-6 bg-white shadow rounded-lg">
          <h3 className="text-sm font-medium text-gray-500">Pending Approvals</h3>
          <p className="text-2xl font-bold">{stats.pending_approvals}</p>
        </div>
      </div>
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">Recent Activity</h2>
        <ul className="divide-y divide-gray-200">
          {stats.recent_activity.map((activity) => (
            <li key={activity.id} className="py-4 flex justify-between">
              <span className="text-gray-900">{activity.action}</span>
              <span className="text-gray-500 text-sm">{activity.time}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
