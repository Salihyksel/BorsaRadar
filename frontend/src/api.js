const API_BASE = 'https://borsaradar-production.up.railway.app/api'

export const fetchKurlar = async () => {
  const res = await fetch(`${API_BASE}/kurlar`)
  return res.json()
}

export const fetchMadenler = async () => {
  const res = await fetch(`${API_BASE}/madenler`)
  return res.json()
}

export const fetchHisseler = async () => {
  const res = await fetch(`${API_BASE}/hisseler`)
  return res.json()
}

export const fetchHaberler = async () => {
  const res = await fetch(`${API_BASE}/haberler`)
  return res.json()
}

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
