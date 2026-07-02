import { useState, useEffect } from 'react'
import Card from '../components/Card'
import { T } from '../theme'
import { fetchHaberler, zamanFormatla } from '../api'

function zamanGoster(zamanStr) {
  const zaman = new Date(zamanStr)
  const simdi = new Date()
  const fark = simdi - zaman
  const dakika = Math.floor(fark / 60000)
  const saat = Math.floor(dakika / 60)
  const gun = Math.floor(saat / 24)

  if (dakika < 1) return 'Az önce'
  if (dakika < 60) return `${dakika} dk önce`
  if (saat < 24) return `${saat} sa önce`
  if (gun < 7) return `${gun} gün önce`

  return zaman.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' })
}

export default function News() {
  const [haberler,   setHaberler]   = useState([])
  const [yukleniyor, setYukleniyor] = useState(true)
  const [filtre,     setFiltre]     = useState('tumu')

  useEffect(() => {
    const yukle = async () => {
      try {
        const data = await fetchHaberler()
        setHaberler(data.map(h => ({ ...h, zaman: zamanFormatla(h.yayin_zamani) })))
      } catch (e) {
        console.error(e)
      } finally {
        setYukleniyor(false)
      }
    }
    yukle()
    const interval = setInterval(yukle, 900000)
    return () => clearInterval(interval)
  }, [])

  const filtreler = [
    { key: 'tumu',    label: 'Tümü'    },
    { key: 'pozitif', label: 'Pozitif' },
    { key: 'negatif', label: 'Negatif' },
    { key: 'notr',    label: 'Nötr'    },
  ]

  const filtreliHaberler = filtre === 'tumu'
    ? haberler
    : haberler.filter(h => h.sentiment === filtre)

  const gruplar = {
    'bugün':    filtreliHaberler.filter(h => h.gun_grubu === 'bugün'),
    'dün':      filtreliHaberler.filter(h => h.gun_grubu === 'dün'),
    'bu_hafta': filtreliHaberler.filter(h => h.gun_grubu === 'bu_hafta'),
  }

  const grupAdi = { 'bugün': 'Bugün', 'dün': 'Dün', 'bu_hafta': 'Bu Hafta' }

  if (yukleniyor) return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      height: '60vh', color: 'rgba(255,255,255,0.4)', fontSize: '14px'
    }}>
      Veriler yükleniyor...
    </div>
  )

  return (
    <div className="page-enter" style={{ padding: '28px 32px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '20px', fontWeight: 500, color: T.textPrimary }}>Haberler</h1>
        <p style={{ fontSize: '12px', color: T.textSecondary, marginTop: '2px' }}>Finansal haberler ve piyasa etkileri</p>
      </div>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
        {filtreler.map(f => (
          <button key={f.key} onClick={() => setFiltre(f.key)} style={{
            padding: '7px 18px', borderRadius: '20px', cursor: 'pointer', fontSize: '13px',
            border: `1px solid ${filtre === f.key ? T.accentBorder : T.cardBorder}`,
            background: filtre === f.key ? T.accentBg : 'transparent',
            color: filtre === f.key ? T.accent : T.textSecondary,
            transition: 'all 0.2s'
          }}>{f.label}</button>
        ))}
      </div>

      {Object.entries(gruplar).map(([grup, grupHaberler]) => {
        if (grupHaberler.length === 0) return null
        return (
          <div key={grup}>
            <div style={{
              fontSize: '11px',
              fontWeight: 600,
              color: T.textSecondary,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              padding: '16px 0 8px',
              borderBottom: `1px solid ${T.cardBorder}`,
              marginBottom: '12px'
            }}>
              {grupAdi[grup]} • {grupHaberler.length} haber
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '24px' }}>
              {grupHaberler.map((h, i) => {
                const sentRenk = h.sentiment === 'pozitif' ? T.green : h.sentiment === 'negatif' ? T.red : 'rgba(255,255,255,0.08)'
                const sentGolge = h.sentiment === 'pozitif' ? 'rgba(16,185,129,0.15)' : h.sentiment === 'negatif' ? 'rgba(244,63,94,0.15)' : 'transparent'
                return (
                  <Card key={h.id} className={`s${(i % 6) + 1} card-enter`}
                    onClick={() => h.url && window.open(h.url, '_blank', 'noopener,noreferrer')}
                    onMouseEnter={e => { if (h.url) e.currentTarget.style.transform = 'translateY(-1px)' }}
                    onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)' }}
                    style={{
                      padding: '16px',
                      border: `1.5px solid ${sentRenk}`,
                      boxShadow: sentGolge !== 'transparent' ? `0 0 12px ${sentGolge}` : 'none',
                      cursor: h.url ? 'pointer' : 'default',
                      transition: 'transform 0.15s ease',
                    }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '6px', marginBottom: '10px' }}>
                      <p style={{ fontSize: '14px', fontWeight: 500, color: T.textPrimary, lineHeight: 1.5, margin: 0, flex: 1 }}>
                        {h.baslik}
                      </p>
                      <span style={{ fontSize: '11px', color: 'rgba(196,181,253,0.4)', flexShrink: 0, marginTop: '3px' }}>↗</span>
                    </div>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '10px' }}>
                      {(h.varliklar || []).map(v => (
                        <span key={v} style={{
                          fontSize: '11px', padding: '2px 8px', borderRadius: '20px',
                          background: T.accentBg, color: T.accent,
                          border: `1px solid ${T.accentBorder}`
                        }}>{v}</span>
                      ))}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '12px', color: T.accent }}>{h.kaynak}</span>
                      <span style={{ fontSize: '12px', color: T.textSecondary }}>{zamanGoster(h.yayin_zamani)}</span>
                    </div>
                  </Card>
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}
