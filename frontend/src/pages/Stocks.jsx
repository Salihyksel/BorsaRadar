import { useState, useMemo, useEffect, useRef } from 'react'
import { createChart, AreaSeries } from 'lightweight-charts'
import Card from '../components/Card'
import { T } from '../theme'
import { fetchHisseler, fetchHaberler, fetchGecmis, zamanFormatla } from '../api'

const SEKTOR_MAP = {
  GARAN: 'Bankacılık', AKBNK: 'Bankacılık', ISCTR: 'Bankacılık',
  YKBNK: 'Bankacılık', VAKBN: 'Bankacılık', HALKB: 'Bankacılık',
  TUPRS: 'Enerji', AKENR: 'Enerji', ZOREN: 'Enerji',
  PETKM: 'Kimya', SODA: 'Kimya',
  ASELS: 'Savunma', RODRG: 'Savunma',
  THYAO: 'Havacılık', PGSUS: 'Havacılık', TAVHL: 'Havacılık', CLEBI: 'Havacılık',
  EREGL: 'Demir-Çelik', KRDMD: 'Demir-Çelik', ISDMR: 'Demir-Çelik',
  KOZAL: 'Madencilik', KOZAA: 'Madencilik', PRKME: 'Madencilik',
  BIMAS: 'Perakende', MGROS: 'Perakende', SOKM: 'Perakende',
  FROTO: 'Otomotiv', TOASO: 'Otomotiv',
  TCELL: 'Telekomünikasyon', TTKOM: 'Telekomünikasyon',
  KCHOL: 'Holding', SAHOL: 'Holding', TKFEN: 'Holding',
  EKGYO: 'GYO', ENKAI: 'İnşaat',
  ULKER: 'Gıda', AEFES: 'Gıda', CCOLA: 'Gıda',
  SISE: 'Cam', TRKCM: 'Cam',
  ARCLK: 'Beyaz Eşya', VESTL: 'Elektronik',
  LOGO: 'Yazılım',
  GUBRF: 'Tarım', TTRAK: 'Tarım',
  TURSG: 'Sigorta', RAYSG: 'Sigorta',
}

const SIRKET_ADLARI = {
  THYAO: 'Türk Hava Yolları', ASELS: 'Aselsan', GARAN: 'Garanti Bankası',
  EREGL: 'Ereğli Demir Çelik', TUPRS: 'Tüpraş', AKBNK: 'Akbank',
  BIMAS: 'BİM Mağazalar', ISCTR: 'İş Bankası', KCHOL: 'Koç Holding',
  SISE: 'Şişecam', TCELL: 'Turkcell', PGSUS: 'Pegasus', VAKBN: 'Vakıfbank',
  ARCLK: 'Arçelik', PETKM: 'Petkim', FROTO: 'Ford Otosan', TOASO: 'Tofaş',
  SAHOL: 'Sabancı Holding', YKBNK: 'Yapı Kredi', HALKB: 'Halkbank',
  EKGYO: 'Emlak Konut', TTKOM: 'Türk Telekom', ENKAI: 'Enka İnşaat',
  TKFEN: 'Tekfen Holding', TAVHL: 'TAV Havalimanları', MGROS: 'Migros',
  ULKER: 'Ülker', KOZAL: 'Koza Altın', KOZAA: 'Koza Anadolu', AEFES: 'Anadolu Efes',
  KRDMD: 'Kardemir', LOGO: 'Logo Yazılım', VESTL: 'Vestel', CCOLA: 'Coca Cola İçecek',
  RODRG: 'Roketsan', AKENR: 'Akenerji', ZOREN: 'Zorlu Enerji', PRKME: 'Park Elektrik',
  GUBRF: 'Gübre Fabrikaları', TTRAK: 'Türk Traktör', ISDMR: 'İskenderun Demir',
  SODA: 'Soda Sanayii', TRKCM: 'Trakya Cam', TURSG: 'Türkiye Sigorta',
  RAYSG: 'Ray Sigorta', CLEBI: 'Çelebi Hava Servisi', SOKM: 'Şok Marketler',
}

function MiniSparkline({ degisim }) {
  const points = Array.from({ length: 20 }, (_, i) => {
    const x = (i / 19) * 60
    const y = 15 - (Math.sin(i * 0.4) * 3 + (i / 19) * (degisim > 0 ? -8 : 8))
    return `${x},${y}`
  }).join(' ')

  return (
    <svg width="60" height="30" style={{ overflow: 'visible', flexShrink: 0 }}>
      <polyline
        points={points}
        fill="none"
        stroke={degisim >= 0 ? '#10b981' : '#f43f5e'}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

const TIMEFRAMES = [
  { key: '1H', label: '1H', days: 7 },
  { key: '1A', label: '1A', days: 30 },
  { key: '3A', label: '3A', days: 90 },
  { key: '6A', label: '6A', days: 180 },
  { key: '1Y', label: '1Y', days: 365 },
  { key: '3Y', label: '3Y', days: 1095 },
]

function StockChart({ hisse }) {
  const containerRef = useRef(null)
  const [timeframe, setTimeframe] = useState('3A')
  const [gecmisVeri, setGecmisVeri] = useState([])

  useEffect(() => {
    let iptal = false
    fetchGecmis(hisse.ticker, timeframe).then(data => {
      if (!iptal && Array.isArray(data)) setGecmisVeri(data)
    })
    return () => { iptal = true }
  }, [hisse.ticker, timeframe])

  useEffect(() => {
    if (!containerRef.current || gecmisVeri.length === 0) return

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 300,
      layout: { background: { color: 'transparent' }, textColor: '#71717a' },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.04)' },
        horzLines: { color: 'rgba(255,255,255,0.04)' },
      },
      crosshair: {
        mode: 1,
        vertLine: { color: '#6366f1', width: 1, style: 3 },
        horzLine: { color: '#6366f1', width: 1, style: 3 },
      },
      rightPriceScale: { borderColor: 'rgba(255,255,255,0.06)', textColor: '#71717a' },
      timeScale: { borderColor: 'rgba(255,255,255,0.06)', timeVisible: true, secondsVisible: false },
    })

    const isPos = hisse.degisim >= 0
    const areaSeries = chart.addSeries(AreaSeries, {
      lineColor:   isPos ? '#10b981' : '#f43f5e',
      topColor:    isPos ? 'rgba(16,185,129,0.3)' : 'rgba(244,63,94,0.3)',
      bottomColor: isPos ? 'rgba(16,185,129,0.0)' : 'rgba(244,63,94,0.0)',
      lineWidth: 2,
    })

    const chartData = gecmisVeri.map(row => ({
      time: row.tarih.includes(' ')
        ? Math.floor(new Date(row.tarih.replace(' ', 'T') + ':00').getTime() / 1000)
        : row.tarih,
      value: row.kapanis,
    }))
    areaSeries.setData(chartData)
    chart.timeScale().fitContent()

    const handleResize = () => {
      if (containerRef.current) chart.applyOptions({ width: containerRef.current.clientWidth })
    }
    window.addEventListener('resize', handleResize)
    return () => { window.removeEventListener('resize', handleResize); chart.remove() }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gecmisVeri])
  return (
    <>
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
      <div ref={containerRef} style={{ width: '100%' }} />
    </>
  )
}

export default function Stocks() {
  const [hisseler,   setHisseler]   = useState([])
  const [haberler,   setHaberler]   = useState([])
  const [yukleniyor, setYukleniyor] = useState(true)
  const [secili,     setSecili]     = useState(null)
  const [aramaMetni, setAramaMetni] = useState('')
  const [sektor,     setSektor]     = useState('Tümü')

  useEffect(() => {
    const yukle = async () => {
      try {
        const [h, hab] = await Promise.all([fetchHisseler(), fetchHaberler()])
        setHisseler(h)
        setHaberler(hab.map(n => ({ ...n, zaman: zamanFormatla(n.yayin_zamani) })))
      } catch (e) {
        console.error(e)
      } finally {
        setYukleniyor(false)
      }
    }
    yukle()
    const interval = setInterval(yukle, 60000)
    return () => clearInterval(interval)
  }, [])

  const hisselerWithSektor = useMemo(() =>
    hisseler.map(h => ({
      ...h,
      degisim: h.degisim_yuzde || 0,
      ad:      SIRKET_ADLARI[h.ticker] || h.ticker,
      sektor:  SEKTOR_MAP[h.ticker]    || 'Diğer',
    })),
  [hisseler])

  const uniqueSektorler = useMemo(() => {
    const set = new Set(hisselerWithSektor.map(h => h.sektor))
    return ['Tümü', ...Array.from(set).sort()]
  }, [hisselerWithSektor])

  const filtreliHisseler = useMemo(() =>
    hisselerWithSektor.filter(h => {
      const aramaUygun = h.ticker.toLowerCase().includes(aramaMetni.toLowerCase()) ||
        h.ad.toLowerCase().includes(aramaMetni.toLowerCase())
      const sektorUygun = sektor === 'Tümü' || h.sektor === sektor
      return aramaUygun && sektorUygun
    }),
  [hisselerWithSektor, aramaMetni, sektor])

  const ilgiliHaberler = secili
    ? haberler.filter(h => h.varliklar && h.varliklar.includes(secili.ticker))
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
    <div className="page-enter" style={{ padding: '28px 32px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ fontSize: '20px', fontWeight: 500, color: T.textPrimary }}>Hisse Senetleri</h1>
        <p style={{ fontSize: '12px', color: T.textSecondary, marginTop: '2px' }}>
          BIST hisseleri ve anlık veriler — {hisselerWithSektor.length} hisse
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '16px', alignItems: 'start' }}>

        <Card className="s1 card-enter" style={{ padding: '16px' }}>
          <div style={{ position: 'relative', marginBottom: '12px' }}>
            <span style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: T.textSecondary, fontSize: '14px' }}>⌕</span>
            <input
              value={aramaMetni}
              onChange={e => setAramaMetni(e.target.value)}
              placeholder="Hisse ara..."
              style={{
                width: '100%', padding: '9px 12px 9px 32px',
                background: T.cardHover, border: `1px solid ${T.cardBorder}`,
                borderRadius: '10px', color: T.textPrimary, fontSize: '13px',
                outline: 'none', boxSizing: 'border-box'
              }}
              onFocus={e => e.target.style.borderColor = T.accentBorder}
              onBlur={e => e.target.style.borderColor = T.cardBorder}
            />
          </div>

          <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap', marginBottom: '12px' }}>
            {uniqueSektorler.map(s => (
              <button key={s} onClick={() => setSektor(s)} style={{
                padding: '3px 8px', borderRadius: '20px', fontSize: '10px', cursor: 'pointer',
                border: `1px solid ${sektor === s ? T.accentBorder : T.cardBorder}`,
                background: sektor === s ? T.accentBg : 'transparent',
                color: sektor === s ? T.accent : T.textSecondary,
                transition: 'all 0.15s'
              }}>{s}</button>
            ))}
          </div>

          <div style={{ maxHeight: 'calc(100vh - 300px)', overflowY: 'auto' }}>
            {filtreliHisseler.map(h => {
              const isPos = h.degisim >= 0
              const isSelected = secili?.ticker === h.ticker
              return (
                <div key={h.ticker} onClick={() => setSecili(h)} style={{
                  display: 'grid', gridTemplateColumns: '1fr 60px auto',
                  alignItems: 'center', gap: '8px',
                  padding: '8px 10px', borderRadius: '10px', cursor: 'pointer',
                  borderLeft: isSelected ? `3px solid ${T.accent}` : '3px solid transparent',
                  background: isSelected ? T.accentBg : 'transparent',
                  transition: 'all 0.15s', marginBottom: '2px'
                }}
                onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = T.cardHover }}
                onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = 'transparent' }}
                >
                  <div style={{ minWidth: 0 }}>
                    <p style={{ fontSize: '13px', fontWeight: 700, color: T.textPrimary, fontFamily: 'monospace', margin: 0 }}>{h.ticker}</p>
                    <p style={{ fontSize: '11px', color: T.textSecondary, margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{h.ad}</p>
                  </div>

                  <MiniSparkline degisim={h.degisim} />

                  <div style={{ textAlign: 'right' }}>
                    <p style={{ fontSize: '13px', fontFamily: 'monospace', color: T.textPrimary, margin: 0 }}>₺{(h.fiyat || 0).toFixed(2)}</p>
                    <span style={{
                      fontSize: '10px', fontWeight: 600,
                      color: isPos ? T.green : T.red,
                      background: isPos ? T.greenBg : T.redBg,
                      padding: '1px 6px', borderRadius: '20px',
                      display: 'inline-block', marginTop: '2px'
                    }}>
                      {isPos ? '+' : ''}{h.degisim.toFixed(2)}%
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </Card>

        {secili ? (
          <div>
            <Card className="s2 card-enter" style={{ padding: '24px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
                <div>
                  <h2 style={{ fontSize: '24px', fontWeight: 600, fontFamily: 'monospace', color: T.textPrimary, margin: 0 }}>{secili.ticker}</h2>
                  <p style={{ fontSize: '14px', color: T.textSecondary, margin: '4px 0 0' }}>{secili.ad} · {secili.sektor}</p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <p style={{ fontSize: '28px', fontWeight: 600, fontFamily: 'monospace', color: T.textPrimary, margin: 0 }}>₺{(secili.fiyat || 0).toFixed(2)}</p>
                  <span style={{
                    fontSize: '14px', color: secili.degisim >= 0 ? T.green : T.red,
                    background: secili.degisim >= 0 ? T.greenBg : T.redBg,
                    padding: '3px 12px', borderRadius: '20px', display: 'inline-block', marginTop: '6px'
                  }}>
                    {secili.degisim >= 0 ? '▲' : '▼'} {Math.abs(secili.degisim).toFixed(2)}%
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '24px', marginBottom: '20px' }}>
                <div>
                  <p style={{ fontSize: '10px', color: T.textSecondary, textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 2px' }}>Hacim</p>
                  <p style={{ fontSize: '13px', fontFamily: 'monospace', color: T.textPrimary, margin: 0 }}>
                    {secili.hacim ? (secili.hacim >= 1000000 ? `${(secili.hacim / 1000000).toFixed(1)}M` : `${(secili.hacim / 1000).toFixed(0)}K`) : '—'}
                  </p>
                </div>
                <div>
                  <p style={{ fontSize: '10px', color: T.textSecondary, textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 2px' }}>Sektör</p>
                  <p style={{ fontSize: '13px', color: T.accent, margin: 0 }}>{secili.sektor}</p>
                </div>
              </div>

              <StockChart hisse={secili} />
            </Card>

            {ilgiliHaberler.length > 0 && (
              <Card style={{ padding: '20px' }}>
                <h3 style={{ fontSize: '14px', fontWeight: 500, color: T.textPrimary, marginBottom: '14px' }}>
                  {secili.ticker} İlgili Haberler
                </h3>
                {ilgiliHaberler.map(h => {
                  const sentRenk = h.sentiment === 'pozitif' ? T.green : h.sentiment === 'negatif' ? T.red : T.textSecondary
                  return (
                    <div key={h.id}
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
                      }}>
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
                })}
              </Card>
            )}
          </div>
        ) : (
          <Card style={{ padding: '60px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
            <span style={{ fontSize: '40px', marginBottom: '12px', opacity: 0.3 }}>◈</span>
            <p style={{ color: T.textSecondary, fontSize: '14px' }}>Listeden bir hisse seçin</p>
          </Card>
        )}

      </div>
    </div>
  )
}
