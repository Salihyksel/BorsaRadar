import { useEffect, useRef } from 'react'

export default function StarfieldBackground() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    let animId

    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()
    window.addEventListener('resize', resize)

    const stars = Array.from({ length: 220 }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      r: Math.random() * 0.9 + 0.1,
      opacity: Math.random() * 0.5 + 0.05,
      twinkleSpeed: Math.random() * 0.015 + 0.003,
      twinkleOffset: Math.random() * Math.PI * 2,
    }))

    const shootingStars = []
    let lastShoot = 0
    let frame = 0

    function createShootingStar() {
      const angle = (Math.random() * 25 + 10) * (Math.PI / 180)
      shootingStars.push({
        x: Math.random() * canvas.width * 0.6 + 50,
        y: Math.random() * canvas.height * 0.35,
        vx: Math.cos(angle) * (5 + Math.random() * 5),
        vy: Math.sin(angle) * (5 + Math.random() * 5),
        life: 1,
        decay: 0.01 + Math.random() * 0.008,
      })
    }

    function draw() {
      frame++
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      stars.forEach(star => {
        const twinkle = Math.sin(frame * star.twinkleSpeed + star.twinkleOffset)
        const op = Math.max(0, star.opacity + twinkle * 0.15)
        ctx.beginPath()
        ctx.arc(star.x, star.y, star.r, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(210, 215, 255, ${op})`
        ctx.fill()
      })

      if (frame - lastShoot > 200 + Math.random() * 280) {
        createShootingStar()
        lastShoot = frame
      }

      for (let i = shootingStars.length - 1; i >= 0; i--) {
        const s = shootingStars[i]
        s.x += s.vx
        s.y += s.vy
        s.life -= s.decay

        if (s.life <= 0) { shootingStars.splice(i, 1); continue }

        const tailLen = 90 + s.life * 60
        const tailX = s.x - s.vx * (tailLen / 8)
        const tailY = s.y - s.vy * (tailLen / 8)

        const grad = ctx.createLinearGradient(tailX, tailY, s.x, s.y)
        grad.addColorStop(0, 'rgba(255,255,255,0)')
        grad.addColorStop(0.6, `rgba(180,190,255,${s.life * 0.35})`)
        grad.addColorStop(1, `rgba(255,255,255,${s.life * 0.85})`)

        ctx.beginPath()
        ctx.moveTo(tailX, tailY)
        ctx.lineTo(s.x, s.y)
        ctx.strokeStyle = grad
        ctx.lineWidth = 1.2
        ctx.stroke()

        ctx.beginPath()
        ctx.arc(s.x, s.y, 1.2, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(255,255,255,${s.life * 0.9})`
        ctx.fill()
      }

      animId = requestAnimationFrame(draw)
    }

    draw()
    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('resize', resize)
    }
  }, [])

  return (
    <canvas ref={canvasRef} style={{
      position: 'fixed', top: 0, left: 0,
      width: '100%', height: '100%',
      pointerEvents: 'none', zIndex: 1,
      opacity: 0.65,
    }} />
  )
}
