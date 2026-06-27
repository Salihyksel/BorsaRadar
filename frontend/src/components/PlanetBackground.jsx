export default function PlanetBackground() {
  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 0,
      pointerEvents: 'none',
      overflow: 'hidden',
      background: '#06060f',
    }}>

      {/* ÜST KÜRE - Mor/İndigo gezegen */}
      <div style={{
        position: 'absolute',
        top: '-45%',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '900px',
        height: '900px',
        borderRadius: '50%',
        background: `radial-gradient(circle at 50% 50%,
          rgba(88, 28, 220, 0.55) 0%,
          rgba(67, 20, 180, 0.40) 25%,
          rgba(80, 40, 180, 0.25) 45%,
          rgba(60, 20, 140, 0.12) 60%,
          transparent 75%
        )`,
        filter: 'blur(20px)',
        animation: 'orbPulse 8s ease-in-out infinite',
      }}/>

      {/* ÜST KÜRE - İnce kenar parlaması */}
      <div style={{
        position: 'absolute',
        top: '-45%',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '900px',
        height: '900px',
        borderRadius: '50%',
        background: `radial-gradient(circle at 50% 100%,
          rgba(200, 150, 255, 0.3) 0%,
          rgba(160, 100, 240, 0.15) 15%,
          transparent 35%
        )`,
        filter: 'blur(8px)',
      }}/>

      {/* ALT KÜRE - Mavi/İndigo gezegen */}
      <div style={{
        position: 'absolute',
        bottom: '-50%',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '1000px',
        height: '1000px',
        borderRadius: '50%',
        background: `radial-gradient(circle at 50% 50%,
          rgba(40, 80, 255, 0.45) 0%,
          rgba(30, 60, 210, 0.30) 25%,
          rgba(20, 40, 180, 0.18) 45%,
          rgba(10, 20, 130, 0.08) 60%,
          transparent 75%
        )`,
        filter: 'blur(25px)',
        animation: 'orbPulseBottom 10s ease-in-out infinite',
      }}/>

      {/* ALT KÜRE - Kenar parlaması */}
      <div style={{
        position: 'absolute',
        bottom: '-50%',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '1000px',
        height: '1000px',
        borderRadius: '50%',
        background: `radial-gradient(circle at 50% 0%,
          rgba(100, 160, 255, 0.25) 0%,
          rgba(60, 120, 240, 0.12) 15%,
          transparent 30%
        )`,
        filter: 'blur(10px)',
      }}/>

      {/* Ortadaki ince horizon çizgisi */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '100%',
        height: '1px',
        background: 'linear-gradient(90deg, transparent, rgba(140,100,255,0.15), rgba(80,130,255,0.15), transparent)',
        filter: 'blur(2px)',
      }}/>

      {/* Çok hafif grid dokusu */}
      <div style={{
        position: 'absolute',
        inset: 0,
        backgroundImage: `radial-gradient(rgba(255,255,255,0.018) 1px, transparent 1px)`,
        backgroundSize: '40px 40px',
      }}/>

    </div>
  )
}
