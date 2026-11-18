import { useEffect, useState } from 'react'

export default function HomePage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-white text-black">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">AgentFlow AI</h1>
        <p className="text-gray-600 mb-6">Autonomous Digital Agency Platform</p>
        <a href="/login" className="inline-block px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
          Sign In
        </a>
      </div>
    </div>
  )
}
