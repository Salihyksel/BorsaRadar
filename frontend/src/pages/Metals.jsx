import { useState, useEffect, useRef } from 'react'
import { createChart, AreaSeries } from 'lightweight-charts'
import Card from '../components/Card'
import { T } from '../theme'
import { fetchMadenler, fetchHaberler, fetchGecmis, zamanFormatla } from '../api'

const MADEN_BILGI = {
  XAU: { ad: 'Altın',    sembol: 'Au', renk: '#f59e0b' },
  XAG: { ad: 'Gümüş',    sembol: 'Ag', renk: '#94a3b8' },
  XPT: { ad: 'Platin',   sembol: 'Pt', renk: '#e2e8f0' },
  XPD: { ad: 'Paladyum', sembol: 'Pd', renk: '#a78bfa' },
}

const TIMEFRAMES = [
  { key: '1H', label: '1H', days: 7 },
  { key: '1A', label: '1A', days: 30 },
  { key: '3A', label: '3A', days: 90 },
  { key: '6A', label: '6A', days: 180 },
  { key: '1Y', label: '1Y', days: 365 },
  { key: '3Y', label: '3Y', days: 1095 },
]

function MetalChart({ maden, timeframe }) {
  const ref = useRef(null)
  const [gecmisVeri, setGecmisVeri] = useState([])

  useEffect(() => {
    let iptal = false
    fetchGecmis(maden.kod, timeframe).then(data => {
      if (!iptal && Array.isArray(data)) setGecmisVeri(data)
    })
    return () => { iptal = true }
  }, [maden.kod, timeframe])

  useEffect(() => {
    if (!ref.current || gecmisVeri.length === 0) return

    const chart = createChart(ref.current, {
      width: ref.current.clientWidth,
      height: 220,
      layout: { background: { color: 'transparent' }, textColor: '#6b6990' },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.03)' },
        horzLines: { color: 'rgba(255,255,255,0.03)' },
      },
      rightPriceScale: { borderColor: 'rgba(255,255,255,0.05)' },
      timeScale: { borderColor: 'rgba(255,255,255,0.05)', timeVisible: true },
    })

    const isPos = maden.degisim >= 0
    const series = chart.addSeries(AreaSeries, {
      lineColor:   isPos ? '#10b981' : '#f43f5e',
      topColor:    isPos ? 'rgba(16,185,129,0.25)' : 'rgba(244,63,94,0.25)',
      bottomColor: 'rgba(0,0,0,0)',
      lineWidth: 2,
    })

    const data = gecmisVeri.map(row => ({
      time: row.tarih.includes(' ')
        ? Math.floor(new Date(row.tarih.replace(' ', 'T') + ':00').getTime() / 1000)
        : row.tarih,
      value: row.kapanis,
    }))

    series.setData(data)
    chart.timeScale().fitContent()

    const handleResize = () => {
      if (ref.current) chart.applyOptions({ width: ref.current.clientWidth })
    }
    window.addEventListener('resize', handleResize)
    return () => { window.removeEventListener('resize', handleResize); chart.remove() }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gecmisVeri])

  return <div ref={ref} style={{ width: '100%' }} />
}

function HaberSatir({ h }) {
  const sentRenk = h.sentiment === 'pozitif' ? T.green : h.sentiment === 'negatif' ? T.red : T.textSecondary
  return (
    <div
      onClick={() => window.open(h.url, '_blank', 'noopener,noreferrer')}
      onMouseEnter={e => { if (h.url) e.currentTarget.style.transform = 'translateY(-1px)' }}
      onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)' }}
      style={{
        padding: '12px', borderRadius: '10px',
        background: 'rgba(255,255,255,0.025)', marginBottom: '8px',
        border: `1px solid ${T.cardBorder}`,
        borderLeft: `3px solid ${sentRenk}`,
        cursor: h.url ? 'pointer' : 'default',
        transition: 'transform 0.15s ease',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '6px' }}>
        <p style={{ fontSize: '13px', color: T.textPrimary, lineHeight: 1.5, margin: 0, flex: 1 }}>{h.baslik}</p>
        <span style={{ fontSize: '11px', color: 'rgba(196,181,253,0.4)', flexShrink: 0, marginTop: '2px' }}>↗</span>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px' }}>
        <span style={{ fontSize: '11px', color: T.accent }}>{h.kaynak}</span>
        <span style={{ fontSize: '11px', color: T.textSecondary }}>{h.zaman}</span>
      </div>
    </div>
  )
}

export default function Metals() {
  const [madenler,   setMadenler]   = useState([])
  const [haberler,   setHaberler]   = useState([])
  const [yukleniyor, setYukleniyor] = useState(true)
  const [seciliMaden, setSeciliMaden] = useState(null)
  const [timeframe,  setTimeframe]  = useState('3A')

  useEffect(() => {
    const yukle = async () => {
      try {
        const [m, hab] = await Promise.all([fetchMadenler(), fetchHaberler()])

        const arr = Object.entries(m).map(([kod, data]) => ({
          kod,
          ad:        MADEN_BILGI[kod]?.ad      || kod,
          sembol:    MADEN_BILGI[kod]?.sembol  || kod,
          renk:      MADEN_BILGI[kod]?.renk    || '#fff',
          usd:       data.fiyat_usd,
          try_fiyat: data.fiyat_try,
          degisim:   data.degisim_yuzde || 0,
          guncelleme: data.guncelleme,
        }))
        setMadenler(arr)
        setSeciliMaden(prev => prev || arr.find(x => x.kod === 'XAU') || arr[0] || null)
        setHaberler(hab.map(n => ({ ...n, zaman: zamanFormatla(n.yayin_zamani) })))
      } catch (e) {
        console.error(e)
      } finally {
        setYukleniyor(false)
      }
    }
    yukle()
    const interval = setInterval(yukle, 300000)
    return () => clearInterval(interval)
  }, [])


  const ilgiliHaberler = seciliMaden
    ? haberler.filter(h =>
        h.varliklar && h.varliklar.some(v =>
          v.toLowerCase().includes(seciliMaden.kod.toLowerCase()) ||
          (seciliMaden.kod === 'XAU' && v === 'altin') ||
          (seciliMaden.kod === 'XAG' && v === 'gumus')
        )
      )
    : []

  if (yukleniyor) return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      height: '60vh', color: 'rgba(255,255,255,0.4)', fontSize: '14px'
    }}>
      Veriler yükleniyor...
    </div>
  )

  return (
    <div className="page-enter page-container" style={{ padding: '28px 32px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '20px', fontWeight: 500, color: T.textPrimary }}>Değerli Madenler</h1>
        <p style={{ fontSize: '12px', color: T.textSecondary, marginTop: '2px' }}>
          {seciliMaden ? `${seciliMaden.ad} seçili · detay görünümü` : 'Anlık spot fiyatlar · Bir madene tıklayın'}
        </p>
      </div>

      {!seciliMaden && (
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '16px', maxWidth: '700px', margin: '0 auto',
        }}>
          {madenler.map((m, i) => {
            const isPos = m.degisim >= 0
            return (
              <Card key={m.kod} className={`s${i + 1} card-enter`} glow topBorder={m.renk}
                onClick={() => setSeciliMaden(m)}
                style={{ padding: '20px', cursor: 'pointer', minHeight: '180px' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <span style={{ fontSize: '20px', fontWeight: 700, fontFamily: 'monospace', color: m.renk }}>{m.sembol}</span>
                      <span style={{ fontSize: '15px', fontWeight: 500, color: T.textPrimary }}>{m.ad}</span>
                    </div>
                    <span style={{ fontSize: '11px', color: T.textSecondary, fontFamily: 'monospace' }}>{m.kod}</span>
                  </div>
                  <span style={{
                    fontSize: '12px', fontWeight: 500,
                    color: isPos ? T.green : T.red,
                    background: isPos ? T.greenBg : T.redBg,
                    padding: '3px 10px', borderRadius: '20px',
                  }}>
                    {isPos ? '+' : ''}{m.degisim.toFixed(2)}%
                  </span>
                </div>
                <p style={{ fontSize: '24px', fontWeight: 600, fontFamily: 'monospace', color: T.textPrimary, marginBottom: '2px' }}>
                  ₺{((m.try_fiyat || 0) / 31.1035).toLocaleString('tr-TR', {maximumFractionDigits: 2})}/gr
                </p>
                <p style={{ fontSize: '13px', color: T.textSecondary }}>
                  ${(m.usd || 0).toLocaleString('tr-TR')} <span style={{ fontSize: '11px' }}>(ons)</span>
                </p>
              </Card>
            )
          })}
        </div>
      )}

      {seciliMaden && (
        <div className="metals-detail-grid" style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '20px', alignItems: 'start' }}>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {madenler.map((m, i) => {
              const isPos = m.degisim >= 0
              const isSelected = seciliMaden?.kod === m.kod
              return (
                <Card key={m.kod} className={`s${i + 1} card-enter`}
                  topBorder={isSelected ? 'rgba(124,58,237,0.7)' : m.renk}
                  onClick={() => setSeciliMaden(isSelected ? null : m)}
                  style={{
                    padding: '12px 14px', cursor: 'pointer',
                    border: isSelected ? '1px solid rgba(124,58,237,0.5)' : undefined,
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '15px', fontWeight: 700, fontFamily: 'monospace', color: m.renk }}>{m.sembol}</span>
                    <div>
                      <p style={{ fontSize: '12px', fontWeight: 500, color: T.textPrimary, margin: 0 }}>{m.ad}</p>
                      <p style={{ fontSize: '10px', color: T.textSecondary, margin: 0 }}>{m.kod}</p>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ fontSize: '12px', fontFamily: 'monospace', color: T.textPrimary, margin: 0 }}>
                      ₺{((m.try_fiyat || 0) / 31.1035).toLocaleString('tr-TR', {maximumFractionDigits: 2})}
                    </p>
                    <span style={{
                      fontSize: '10px', fontWeight: 600,
                      color: isPos ? T.green : T.red,
                      background: isPos ? T.greenBg : T.redBg,
                      padding: '1px 6px', borderRadius: '20px',
                      display: 'inline-block', marginTop: '2px',
                    }}>
                      {isPos ? '+' : ''}{m.degisim.toFixed(2)}%
                    </span>
                  </div>
                </Card>
              )
            })}
          </div>

          <div>
            <Card style={{ padding: '20px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '26px', fontWeight: 700, fontFamily: 'monospace', color: seciliMaden.renk }}>{seciliMaden.sembol}</span>
                    <h2 style={{ fontSize: '20px', fontWeight: 600, color: T.textPrimary, margin: 0 }}>{seciliMaden.ad}</h2>
                  </div>
                  <p style={{ fontSize: '13px', color: T.textSecondary, margin: '4px 0 0' }}>{seciliMaden.kod} · Troy Ons</p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <p style={{ fontSize: '26px', fontWeight: 600, fontFamily: 'monospace', color: T.textPrimary, margin: 0 }}>
                    ₺{((seciliMaden.try_fiyat || 0) / 31.1035).toLocaleString('tr-TR', {maximumFractionDigits: 2})}/gr
                  </p>
                  <p style={{ fontSize: '13px', color: T.textSecondary, margin: '2px 0 0' }}>
                    ${(seciliMaden.usd || 0).toLocaleString('tr-TR')} (ons)
                  </p>
                  <span style={{
                    fontSize: '13px',
                    color: seciliMaden.degisim >= 0 ? T.green : T.red,
                    background: seciliMaden.degisim >= 0 ? T.greenBg : T.redBg,
                    padding: '3px 12px', borderRadius: '20px',
                    display: 'inline-block', marginTop: '6px',
                  }}>
                    {seciliMaden.degisim >= 0 ? '▲' : '▼'} {Math.abs(seciliMaden.degisim).toFixed(2)}%
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.5)' }}>Fiyat Grafiği</span>
                <div style={{ display: 'flex', gap: '4px' }}>
                  {TIMEFRAMES.map(tf => (
                    <button key={tf.key} onClick={() => setTimeframe(tf.key)} style={{
                      padding: '3px 9px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer',
                      background: timeframe === tf.key ? 'rgba(124,58,237,0.3)' : 'transparent',
                      border: `1px solid ${timeframe === tf.key ? 'rgba(124,58,237,0.5)' : 'rgba(255,255,255,0.08)'}`,
                      color: timeframe === tf.key ? '#c4b5fd' : 'rgba(255,255,255,0.4)',
                      transition: 'all 0.15s',
                    }}>
                      {tf.label}
                    </button>
                  ))}
                </div>
              </div>

              <MetalChart maden={seciliMaden} timeframe={timeframe} />
            </Card>

            {ilgiliHaberler.length > 0 && (
              <Card style={{ padding: '20px' }}>
                <h3 style={{ fontSize: '14px', fontWeight: 500, color: T.textPrimary, marginBottom: '14px' }}>
                  {seciliMaden.ad} İlgili Haberler
                </h3>
                {ilgiliHaberler.map(h => <HaberSatir key={h.id} h={h} />)}
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
