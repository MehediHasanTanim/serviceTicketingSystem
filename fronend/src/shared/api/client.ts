const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8011/api/v1'

export async function apiRequest(path: string, options: RequestInit = {}) {
  const url = `${baseUrl}${path}`
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })

  if (response.status === 204) {
    return null
  }

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const message = data?.detail || data?.message || 'Request failed'
    const error = new Error(message)
    error.details = data
    throw error
  }

  return data
}
