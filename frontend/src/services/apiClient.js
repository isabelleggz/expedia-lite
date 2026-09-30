const API_BASE_PATH = import.meta.env.VITE_API_BASE_PATH || '/api/v1'

export class ApiRequestError extends Error {
  constructor(message, { code = '', status = 0 } = {}) {
    super(message)
    this.name = 'ApiRequestError'
    this.code = code
    this.status = status
  }
}

function apiPath(path) {
  return `${API_BASE_PATH}${path}`
}

async function responseError(response, fallbackMessage) {
  try {
    const body = await response.json()
    if (
      body.error &&
      typeof body.error.code === 'string' &&
      typeof body.error.message === 'string'
    ) {
      return new ApiRequestError(body.error.message, {
        code: body.error.code,
        status: response.status,
      })
    }
    if (typeof body.detail === 'string' && body.detail) {
      return new ApiRequestError(body.detail, { status: response.status })
    }
  } catch {
    // The fallback remains clearer than exposing a response parsing failure.
  }

  return new ApiRequestError(fallbackMessage, { status: response.status })
}

export async function requestJson(path, options, fallbackMessage) {
  return requestBackendJson(apiPath(path), options, fallbackMessage)
}

export async function requestBackendJson(path, options, fallbackMessage) {
  const response = await fetch(path, options)

  if (!response.ok) {
    throw await responseError(response, fallbackMessage)
  }

  if (response.status === 204) {
    return null
  }

  return response.json()
}
