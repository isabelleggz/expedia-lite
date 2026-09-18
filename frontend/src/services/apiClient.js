const API_BASE_PATH = import.meta.env.VITE_API_BASE_PATH || '/api/v1'

function apiPath(path) {
  return `${API_BASE_PATH}${path}`
}

async function responseError(response, fallbackMessage) {
  try {
    const body = await response.json()
    if (typeof body.detail === 'string' && body.detail) {
      return new Error(body.detail)
    }
  } catch {
    // The fallback remains clearer than exposing a response parsing failure.
  }

  return new Error(fallbackMessage)
}

export async function requestJson(path, options, fallbackMessage) {
  const response = await fetch(apiPath(path), options)

  if (!response.ok) {
    throw await responseError(response, fallbackMessage)
  }

  if (response.status === 204) {
    return null
  }

  return response.json()
}
