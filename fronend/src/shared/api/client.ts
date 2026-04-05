const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8011/api/v1'

export async function apiRequest(path: string, options: RequestInit = {}) {
  const url = `${baseUrl}${path}`
  const headers = new Headers({
    'Content-Type': 'application/json',
  })
  if (options.headers) {
    const extra = new Headers(options.headers)
    extra.forEach((value, key) => headers.set(key, value))
  }
  const response = await fetch(url, {
    ...options,
    headers,
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
