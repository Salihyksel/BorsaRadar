import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { useState, useEffect } from 'react'
import PlanetBackground from './components/PlanetBackground'
import NetworkBackground from './components/NetworkBackground'
import StarfieldBackground from './components/StarfieldBackground'
import Dashboard from './pages/Dashboard'
import Stocks from './pages/Stocks'
import Metals from './pages/Metals'
import News from './pages/News'

function Navbar() {
  const [time, setTime] = useState(new Date())
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  const navItems = [
    { to: '/dashboard', label: 'Ana Sayfa', emoji: '⌂' },
    { to: '/stocks', label: 'Hisse Senetleri', emoji: '◈' },
    { to: '/metals', label: 'Değerli Madenler', emoji: '◆' },
    { to: '/news', label: 'Haberler', emoji: '◎' },
  ]

  return (
    <nav style={{
      position: 'fixed', top: 0, left: 0, right: 0,
      height: '62px', zIndex: 100,
      background: 'rgba(6,6,15,0.75)',
      borderBottom: '1px solid rgba(255,255,255,0.07)',
      backdropFilter: 'blur(30px)',
      WebkitBackdropFilter: 'blur(30px)',
      display: 'flex', alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 32px',
      animation: 'navReveal 0.6s cubic-bezier(0.16,1,0.3,1) both',
    }}>

      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '9px' }}>
        <div style={{
          width: '28px', height: '28px',
          borderRadius: '8px',
          background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
          display: 'flex', alignItems: 'center',
          justifyContent: 'center',
          fontSize: '14px',
          boxShadow: '0 0 20px rgba(124,58,237,0.4)',
        }}>◉</div>
        <span className="top-navbar-logo-text" style={{
          fontSize: '15px', fontWeight: 600,
          background: 'linear-gradient(135deg, #c4b5fd, #818cf8)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          letterSpacing: '0.02em',
        }}>BorsaRadar</span>
      </div>

      {/* Tabs */}
      <div className="desktop-nav-tabs" style={{
        gap: '2px',
        background: 'rgba(255,255,255,0.04)',
        padding: '4px',
        borderRadius: '12px',
        border: '1px solid rgba(255,255,255,0.06)',
      }}>
        {navItems.map(item => (
          <NavLink key={item.to} to={item.to} style={({ isActive }) => ({
            padding: '6px 16px',
            borderRadius: '8px',
            fontSize: '13px',
            fontWeight: isActive ? 500 : 400,
            color: isActive ? '#c4b5fd' : 'rgba(255,255,255,0.45)',
            background: isActive
              ? 'rgba(124,58,237,0.25)'
              : 'transparent',
            border: isActive
              ? '1px solid rgba(124,58,237,0.35)'
              : '1px solid transparent',
            textDecoration: 'none',
            transition: 'all 0.2s ease',
            display: 'flex', alignItems: 'center', gap: '5px',
            backdropFilter: isActive ? 'blur(10px)' : 'none',
          })}>
            <span style={{ fontSize: '12px' }}>{item.emoji}</span>
            {item.label}
          </NavLink>
        ))}
      </div>

      {/* Live clock */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={{
          width: '7px', height: '7px', borderRadius: '50%',
          background: '#10b981',
          animation: 'pulse 2s infinite',
          boxShadow: '0 0 8px #10b981',
        }}/>
        <span className="top-navbar-clock-text" style={{
          fontSize: '12px',
          color: 'rgba(255,255,255,0.4)',
          fontVariantNumeric: 'tabular-nums',
          letterSpacing: '0.02em',
        }}>
          Canlı • {time.toLocaleTimeString('tr-TR', {
            hour: '2-digit', minute: '2-digit', second: '2-digit'
          })}
        </span>
      </div>
    </nav>
  )
}

function MobileTabBar() {
  const navItems = [
    { to: '/dashboard', label: 'Ana Sayfa', emoji: '⌂' },
    { to: '/stocks', label: 'Hisseler', emoji: '◈' },
    { to: '/metals', label: 'Madenler', emoji: '◆' },
    { to: '/news', label: 'Haberler', emoji: '◎' },
  ]

  return (
    <nav className="mobile-bottom-tabbar" style={{
      position: 'fixed', bottom: 0, left: 0, right: 0,
      height: '64px', zIndex: 100,
      background: 'rgba(6,6,15,0.92)',
      borderTop: '1px solid rgba(255,255,255,0.08)',
      backdropFilter: 'blur(30px)',
      WebkitBackdropFilter: 'blur(30px)',
      alignItems: 'center',
      justifyContent: 'space-around',
      paddingBottom: 'env(safe-area-inset-bottom)',
    }}>
      {navItems.map(item => (
        <NavLink key={item.to} to={item.to} style={({ isActive }) => ({
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px',
          textDecoration: 'none',
          color: isActive ? '#c4b5fd' : 'rgba(255,255,255,0.45)',
          flex: 1,
          padding: '6px 0',
        })}>
          <span style={{ fontSize: '18px' }}>{item.emoji}</span>
          <span style={{ fontSize: '10px', fontWeight: 500 }}>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  )
}

function App() {
  return (
    <BrowserRouter>
      {/* Katman 1: Gezegen arka planı */}
      <PlanetBackground />

      {/* Katman 2: Network particle */}
      <NetworkBackground />

      {/* Katman 3: Yıldız alanı */}
      <StarfieldBackground />

      {/* Katman 3: UI */}
      <div className="app-content-wrapper" style={{ position: 'relative', zIndex: 2, paddingTop: '62px' }}>
        <Navbar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/stocks" element={<Stocks />} />
          <Route path="/metals" element={<Metals />} />
          <Route path="/news" element={<News />} />
        </Routes>
        <MobileTabBar />
      </div>
    </BrowserRouter>
  )
}

export default App
