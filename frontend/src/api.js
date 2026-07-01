const API_BASE = 'https://borsaradar-production.up.railway.app/api'

// Cache sistemi — 60 saniye TTL
const cache = {}
const CACHE_TTL = 60 * 1000

async function fetchWithCache(key, url) {
  const now = Date.now()
  if (cache[key] && now - cache[key].ts < CACHE_TTL) {
    return cache[key].data
  }
  const res = await fetch(url)
  const data = await res.json()
  cache[key] = { data, ts: now }
  return data
}

export const fetchKurlar = () => fetchWithCache('kurlar', `${API_BASE}/kurlar`)
export const fetchMadenler = () => fetchWithCache('madenler', `${API_BASE}/madenler`)
export const fetchHisseler = () => fetchWithCache('hisseler', `${API_BASE}/hisseler`)
export const fetchHaberler = () => fetchWithCache('haberler', `${API_BASE}/haberler`)

export function zamanFormatla(isoStr) {
  if (!isoStr) return '—'
  const diff = Date.now() - new Date(isoStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'şimdi'
  if (mins < 60) return `${mins}dk önce`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}s önce`
  return `${Math.floor(hours / 24)}g önce`
}

export const fetchGecmis = async (sembol, period = '3A') => {
  const res = await fetch(`${API_BASE}/gecmis/${sembol}?period=${period}`)
  return res.json()
}
