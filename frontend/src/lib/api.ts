
const API_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1'

const TOKEN_KEY = 'agentflow_access_token'

export function saveToken(token: string) {
  sessionStorage.setItem(TOKEN_KEY, token)
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return sessionStorage.getItem(TOKEN_KEY)
}

export function logout() {
  sessionStorage.removeItem(TOKEN_KEY)
  window.location.href = '/login'
}

export async function login(email: string, password: string) {
  const formData = new URLSearchParams()
  formData.set('username', email)
  formData.set('password', password)

  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData,
  })

  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.detail || 'Login failed')
  }

  saveToken(data.access_token)
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers)
  const token = getToken()

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers.has('Content-Type')
  ) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  })

  if (response.status === 401) {
    logout()
    throw new Error('Session expired. Please log in again.')
  }

  if (!response.ok) {
    throw new Error(await response.text())
  }

  return response.json() as Promise<T>
}

