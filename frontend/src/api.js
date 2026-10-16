
import axios from 'axios'

const DEVICE_ID_KEY = 'zapuzaDeviceId'

function getDeviceId() {
  let deviceId = localStorage.getItem(DEVICE_ID_KEY)

  if (!deviceId) {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      deviceId = crypto.randomUUID()
    } else {
      deviceId = `device-${Date.now()}-${Math.random()
        .toString(36)
        .slice(2)}`
    }

    localStorage.setItem(DEVICE_ID_KEY, deviceId)
  }

  return deviceId
}

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken')

  if (token) {
    config.headers.Authorization = `Token ${token}`
  }

  config.headers['X-Device-ID'] = getDeviceId()

  return config
})

export default api
