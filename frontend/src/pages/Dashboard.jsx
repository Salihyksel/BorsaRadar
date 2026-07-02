import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import Card from '../components/Card'
import { T } from '../theme'
import { fetchKurlar, fetchMadenler, fetchHisseler, fetchHaberler, zamanFormatla } from '../api'

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

const MADEN_BILGI = {
  XAU: { ad: 'Altın',   sembol: 'Au', renk: '#f59e0b' },
  XAG: { ad: 'Gümüş',   sembol: 'Ag', renk: '#94a3b8' },
  XPT: { ad: 'Platin',  sembol: 'Pt', renk: '#e2e8f0' },
  XPD: { ad: 'Paladyum',sembol: 'Pd', renk: '#a78bfa' },
}

function PiyasaGenislikBar({ hisseler }) {
  const yukselenSayi   = hisseler.filter(h => h.degisim > 0).length
  const dusenSayi      = hisseler.filter(h => h.degisim < 0).length
  const degismediSayi  = hisseler.filter(h => h.degisim === 0).length
  const toplamSayi     = hisseler.length || 1
  const yukselenPct    = (yukselenSayi  / toplamSayi) * 100
  const dusenPct       = (dusenSayi     / toplamSayi) * 100
  const degismediPct   = (degismediSayi / toplamSayi) * 100

  return (
    <Card style={{ padding: '16px 20px', marginBottom: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
        <p style={{ fontSize: '11px', color: T.textSecondary, textTransform: 'uppercase', letterSpacing: '0.06em', margin: 0 }}>
          Piyasa Genişliği — {toplamSayi} hisse
        </p>
        <div style={{ display: 'flex', gap: '16px', fontSize: '12px' }}>
          <span style={{ color: '#10b981', fontWeight: 600 }}>▲ {yukselenSayi} yükselen</span>
          <span style={{ color: '#f43f5e', fontWeight: 600 }}>▼ {dusenSayi} düşen</span>
          {degismediSayi > 0 && (
            <span style={{ color: T.textSecondary }}>— {degismediSayi} değişmedi</span>
          )}
        </div>
      </div>
      <div style={{ display: 'flex', height: '6px', borderRadius: '6px', overflow: 'hidden', gap: '2px' }}>
        <div style={{ width: `${yukselenPct}%`, background: '#10b981', borderRadius: '6px 0 0 6px', transition: 'width 0.5s ease' }} />
        {degismediPct > 0 && (
          <div style={{ width: `${degismediPct}%`, background: T.textMuted }} />
        )}
        <div style={{ width: `${dusenPct}%`, background: '#f43f5e', borderRadius: '0 6px 6px 0', transition: 'width 0.5s ease' }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px' }}>
        <span style={{ fontSize: '10px', color: '#10b981' }}>{yukselenPct.toFixed(0)}%</span>
        <span style={{ fontSize: '10px', color: '#f43f5e' }}>{dusenPct.toFixed(0)}%</span>
      </div>
    </Card>
  )
}

function KPIKart({ label, deger, alt, degisim, renkTop, className }) {
  const isPos = degisim >= 0
  return (
    <Card glow className={className} topBorder={renkTop} style={{ padding: '20px' }}>
      <p style={{ fontSize: '11px', color: T.textSecondary, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '10px' }}>
        {label}
      </p>
      <p style={{
        fontSize: '26px', fontWeight: 600,
        fontVariantNumeric: 'tabular-nums',
        letterSpacing: '-0.5px',
        color: T.textPrimary, marginBottom: '6px'
      }}>{deger}</p>
      {alt && <p style={{ fontSize: '12px', color: T.textSecondary, marginBottom: '4px' }}>{alt}</p>}
      <span style={{
        fontSize: '12px', fontWeight: 500,
        color: isPos ? T.green : T.red,
        background: isPos ? T.greenBg : T.redBg,
        padding: '2px 8px', borderRadius: '20px',
        display: 'inline-block'
      }}>
        {isPos ? '▲' : '▼'} {Math.abs(degisim).toFixed(2)}%
      </span>
    </Card>
  )
}

function HisseSatir({ h }) {
  const isPos = h.degisim >= 0
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '9px 12px', borderRadius: '10px',
      transition: 'background 0.15s', cursor: 'pointer'
    }}
    onMouseEnter={e => e.currentTarget.style.background = T.cardHover}
    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
    >
      <div>
        <span style={{ fontSize: '13px', fontWeight: 600, color: T.textPrimary, fontFamily: 'monospace' }}>{h.ticker}</span>
        <span style={{ fontSize: '11px', color: T.textSecondary, marginLeft: '8px' }}>{h.ad}</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <span style={{ fontSize: '13px', fontFamily: 'monospace', color: T.textPrimary }}>
          ₺{(h.fiyat || 0).toFixed(2)}
        </span>
        <span style={{
          fontSize: '11px', fontWeight: 500,
          color: isPos ? T.green : T.red,
          background: isPos ? T.greenBg : T.redBg,
          padding: '2px 7px', borderRadius: '20px', minWidth: '52px', textAlign: 'center'
        }}>
          {isPos ? '+' : ''}{h.degisim.toFixed(2)}%
        </span>
      </div>
    </div>
  )
}

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

function HaberKart({ haber }) {
  const sentRenk = haber.sentiment === 'pozitif' ? T.green : haber.sentiment === 'negatif' ? T.red : T.textSecondary
  return (
    <div
      onClick={() => window.open(haber.url, '_blank', 'noopener,noreferrer')}
      onMouseEnter={e => { if (haber.url) e.currentTarget.style.transform = 'translateY(-1px)' }}
      onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)' }}
      style={{
        display: 'flex', gap: '12px', padding: '12px',
        background: 'rgba(255,255,255,0.025)', borderRadius: '12px',
        border: `1px solid ${T.cardBorder}`,
        borderLeft: `3px solid ${sentRenk}`,
        marginBottom: '8px',
        cursor: haber.url ? 'pointer' : 'default',
        transition: 'transform 0.15s ease',
      }}>
      <div style={{
        width: '48px', height: '48px', borderRadius: '8px', flexShrink: 0,
        background: 'linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.1))',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '18px', color: T.accent, overflow: 'hidden'
      }}>
        {haber.url ? (
          <img
            src={`https://www.google.com/s2/favicons?domain=${new URL(haber.url).hostname}&sz=64`}
            alt=""
            style={{ width: '24px', height: '24px' }}
            onError={e => { e.target.style.display = 'none'; e.target.parentElement.textContent = '◎' }}
          />
        ) : '◎'}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '6px', marginBottom: '4px' }}>
          <p style={{
            fontSize: '13px', color: T.textPrimary, lineHeight: 1.5, margin: 0, flex: 1,
            overflow: 'hidden', display: '-webkit-box',
            WebkitLineClamp: 2, WebkitBoxOrient: 'vertical'
          }}>{haber.baslik}</p>
          <span style={{ fontSize: '11px', color: 'rgba(196,181,253,0.4)', flexShrink: 0, marginTop: '2px' }}>↗</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '11px', color: T.accent }}>{haber.kaynak}</span>
          <span style={{ fontSize: '11px', color: T.textSecondary }}>{zamanGoster(haber.yayin_zamani)}</span>
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [kurlar,   setKurlar]   = useState({ USD_TRY: 0, EUR_TRY: 0 })
  const [madenler, setMadenler] = useState([])
  const [hisseler, setHisseler] = useState([])
  const [haberler, setHaberler] = useState([])
  const [yukleniyor, setYukleniyor] = useState(true)
  const [haberIndex, setHaberIndex] = useState(0)

  const veriYukle = async () => {
    try {
      const [k, m, h, hab] = await Promise.all([
        fetchKurlar(), fetchMadenler(), fetchHisseler(), fetchHaberler()
      ])
      setKurlar(k)

      const madenArr = Object.entries(m).map(([kod, data]) => ({
        kod,
        ad:       MADEN_BILGI[kod]?.ad      || kod,
        sembol:   MADEN_BILGI[kod]?.sembol  || kod,
        renk:     MADEN_BILGI[kod]?.renk    || '#fff',
        usd:      data.fiyat_usd,
        try_fiyat:data.fiyat_try,
        degisim:  data.degisim_yuzde || 0,
        guncelleme: data.guncelleme,
      }))
      setMadenler(madenArr)

      const hisselerNorm = h.map(s => ({
        ...s,
        ad:      SIRKET_ADLARI[s.ticker] || s.ticker,
        degisim: s.degisim_yuzde || 0,
      }))
      setHisseler(hisselerNorm)

      const haberlerNorm = hab.map(n => ({
        ...n,
        zaman: zamanFormatla(n.yayin_zamani),
      }))
      setHaberler(haberlerNorm)
    } catch (e) {
      console.error('Veri yükleme hatası:', e)
    } finally {
      setYukleniyor(false)
    }
  }

  useEffect(() => {
    veriYukle()
    const interval = setInterval(veriYukle, 60000)
    return () => clearInterval(interval)
  }, [])

  if (yukleniyor) return (
    <div style={{
      display: 'flex', alignItems: 'center',
      justifyContent: 'center', height: '60vh',
      color: 'rgba(255,255,255,0.4)', fontSize: '14px'
    }}>
      Veriler yükleniyor...
    </div>
  )

  const altin = madenler.find(m => m.kod === 'XAU') || {}
  const gumus = madenler.find(m => m.kod === 'XAG') || {}
  const usd = kurlar.USD_TRY || 0
  const eur = kurlar.EUR_TRY || 0
  const usd_degisim = kurlar.usd_degisim || 0
  const eur_degisim = kurlar.eur_degisim || 0

  const gorHaberler = haberler.slice(haberIndex * 3, haberIndex * 3 + 3)
  const maxIndex    = Math.max(0, Math.floor(haberler.length / 3) - 1)

  return (
    <div className="page-enter page-container" style={{ padding: '28px 32px', maxWidth: '1400px', margin: '0 auto' }}>

      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1 style={{ fontSize: '20px', fontWeight: 500, color: T.textPrimary }}>Piyasa Özeti</h1>
            <p style={{ fontSize: '12px', color: T.textSecondary, marginTop: '2px' }}>
              {new Date().toLocaleDateString('tr-TR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
            </p>
          </div>
          <div style={{ fontSize: '11px', color: T.textSecondary, textAlign: 'right', marginTop: '4px' }}>
            Son güncelleme: {
              hisseler[0]?.guncelleme
                ? new Date(hisseler[0].guncelleme).toLocaleTimeString('tr-TR')
                : '—'
            }
            <span style={{ marginLeft: '8px', color: T.green, fontSize: '10px' }}>● Canlı</span>
          </div>
        </div>
      </div>

      <PiyasaGenislikBar hisseler={hisseler} />

      <div className="kpi-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px', marginBottom: '20px' }}>
        <KPIKart className="s1 card-enter" label="USD / TRY" deger={usd.toFixed(4)} degisim={usd_degisim} renkTop='rgba(99,102,241,0.6)' />
        <KPIKart className="s2 card-enter" label="EUR / TRY" deger={eur.toFixed(4)} degisim={eur_degisim} renkTop='rgba(99,102,241,0.6)' />
        <KPIKart className="s3 card-enter" label="Altın (gr)"
          deger={altin.try_fiyat ? `₺${(altin.try_fiyat / 31.1).toFixed(0)}` : '—'}
          alt={altin.usd ? `$${(altin.usd / 31.1).toFixed(2)}/gr` : undefined}
          degisim={altin.degisim || 0}
          renkTop='rgba(245,158,11,0.6)' />
        <KPIKart className="s4 card-enter" label="Gümüş (gr)"
          deger={gumus.try_fiyat ? `₺${(gumus.try_fiyat / 31.1).toFixed(1)}` : '—'}
          alt={gumus.usd ? `$${(gumus.usd / 31.1).toFixed(2)}/gr` : undefined}
          degisim={gumus.degisim || 0}
          renkTop='rgba(148,163,184,0.6)' />
      </div>

      <div className="grid-2col" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>

        <Card className="s5 card-enter" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '14px', fontWeight: 500, color: T.textPrimary }}>Öne Çıkan Hisseler</h2>
            <Link to="/stocks" style={{ fontSize: '12px', color: T.accent, textDecoration: 'none' }}>
              Tümü →
            </Link>
          </div>
          {hisseler.slice(0, 8).map(h => <HisseSatir key={h.ticker} h={h} />)}
        </Card>

        <Card className="s6 card-enter" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '14px', fontWeight: 500, color: T.textPrimary }}>Son Haberler</h2>
            <div style={{ display: 'flex', gap: '6px' }}>
              {[0, 1, 2].map(i => (
                <div key={i} onClick={() => setHaberIndex(i)} style={{
                  width: '6px', height: '6px', borderRadius: '50%', cursor: 'pointer',
                  background: haberIndex === i ? T.accent : T.textMuted,
                  transition: 'background 0.2s'
                }}/>
              ))}
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '6px', marginBottom: '12px' }}>
            <button onClick={() => setHaberIndex(Math.max(0, haberIndex - 1))} style={{
              width: '28px', height: '28px', borderRadius: '8px', border: `1px solid ${T.cardBorder}`,
              background: 'transparent', color: T.textSecondary, cursor: 'pointer', fontSize: '14px'
            }}>‹</button>
            <button onClick={() => setHaberIndex(Math.min(maxIndex, haberIndex + 1))} style={{
              width: '28px', height: '28px', borderRadius: '8px', border: `1px solid ${T.cardBorder}`,
              background: 'transparent', color: T.textSecondary, cursor: 'pointer', fontSize: '14px'
            }}>›</button>
          </div>
          <div style={{ transition: 'opacity 0.3s' }}>
            {gorHaberler.map(h => <HaberKart key={h.id} haber={h} />)}
          </div>
        </Card>

      </div>
    </div>
  )
}
