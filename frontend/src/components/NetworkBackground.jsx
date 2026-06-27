import { useEffect, useRef } from 'react'

export default function NetworkBackground() {
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

    const fixedNodes = [
      { x: 0.5,  y: 0.45, size: 3   }, // IST
      { x: 0.15, y: 0.35, size: 3.5 }, // NY
      { x: 0.28, y: 0.25, size: 3   }, // LON
      { x: 0.72, y: 0.3,  size: 3   }, // TOK
      { x: 0.65, y: 0.4,  size: 2.5 }, // HK
      { x: 0.35, y: 0.22, size: 2.5 }, // PAR
      { x: 0.82, y: 0.5,  size: 2   }, // SYD
      { x: 0.6,  y: 0.6,  size: 2.5 }, // DXB
    ]

    const nodes = [
      ...fixedNodes.map(n => ({
        x: n.x * window.innerWidth,
        y: n.y * window.innerHeight,
        vx: (Math.random() - 0.5) * 0.15,
        vy: (Math.random() - 0.5) * 0.15,
        r: n.size,
        fixed: true,
        pulse: 0,
        pulseSpeed: Math.random() * 0.03 + 0.01,
      })),
      ...Array.from({ length: 35 }, () => ({
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        r: Math.random() * 1.5 + 0.5,
        fixed: false,
        pulse: Math.random() * Math.PI * 2,
        pulseSpeed: Math.random() * 0.02 + 0.005,
      })),
    ]

    const dataFlows = []
    let lastFlow = 0
    let frame = 0

    function createDataFlow() {
      const from = Math.floor(Math.random() * fixedNodes.length)
      let to = Math.floor(Math.random() * fixedNodes.length)
      if (to === from) to = (to + 1) % fixedNodes.length
      dataFlows.push({
        fromIdx: from,
        toIdx: to,
        progress: 0,
        speed: 0.008 + Math.random() * 0.006,
      })
    }

    function draw() {
      frame++
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x
          const dy = nodes[i].y - nodes[j].y
          const dist = Math.sqrt(dx * dx + dy * dy)
          const maxDist = nodes[i].fixed && nodes[j].fixed ? 350 : 180

          if (dist < maxDist) {
            const opacity = (1 - dist / maxDist) * 0.12
            ctx.beginPath()
            ctx.moveTo(nodes[i].x, nodes[i].y)
            ctx.lineTo(nodes[j].x, nodes[j].y)
            ctx.strokeStyle = `rgba(120, 80, 220, ${opacity})`
            ctx.lineWidth = nodes[i].fixed && nodes[j].fixed ? 0.8 : 0.4
            ctx.stroke()
          }
        }
      }

      if (frame - lastFlow > 120) {
        createDataFlow()
        lastFlow = frame
      }

      for (let i = dataFlows.length - 1; i >= 0; i--) {
        const flow = dataFlows[i]
        flow.progress += flow.speed
        if (flow.progress >= 1) { dataFlows.splice(i, 1); continue }

        const fromNode = nodes[flow.fromIdx]
        const toNode = nodes[flow.toIdx]
        const x = fromNode.x + (toNode.x - fromNode.x) * flow.progress
        const y = fromNode.y + (toNode.y - fromNode.y) * flow.progress

        ctx.beginPath()
        ctx.arc(x, y, 2, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(160, 120, 255, ${0.8 * (1 - Math.abs(flow.progress - 0.5) * 2)})`
        ctx.fill()

        const tailProgress = Math.max(0, flow.progress - 0.08)
        const tailX = fromNode.x + (toNode.x - fromNode.x) * tailProgress
        const tailY = fromNode.y + (toNode.y - fromNode.y) * tailProgress
        const tailGrad = ctx.createLinearGradient(tailX, tailY, x, y)
        tailGrad.addColorStop(0, 'rgba(140, 90, 255, 0)')
        tailGrad.addColorStop(1, 'rgba(160, 120, 255, 0.4)')
        ctx.beginPath()
        ctx.moveTo(tailX, tailY)
        ctx.lineTo(x, y)
        ctx.strokeStyle = tailGrad
        ctx.lineWidth = 1.5
        ctx.stroke()
      }

      nodes.forEach(node => {
        node.pulse += node.pulseSpeed
        const pulseScale = 1 + Math.sin(node.pulse) * 0.3

        if (node.fixed) {
          ctx.beginPath()
          ctx.arc(node.x, node.y, node.r * 2.5 * pulseScale, 0, Math.PI * 2)
          ctx.fillStyle = 'rgba(130, 90, 255, 0.08)'
          ctx.fill()

          ctx.beginPath()
          ctx.arc(node.x, node.y, node.r, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(170, 130, 255, ${0.6 + Math.sin(node.pulse) * 0.2})`
          ctx.fill()
        } else {
          ctx.beginPath()
          ctx.arc(node.x, node.y, node.r, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(120, 80, 200, ${0.25 + Math.sin(node.pulse) * 0.1})`
          ctx.fill()
        }

        node.x += node.vx
        node.y += node.vy
        if (node.x < 0 || node.x > canvas.width)  node.vx *= -1
        if (node.y < 0 || node.y > canvas.height) node.vy *= -1
      })

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
      position: 'fixed',
      top: 0, left: 0,
      width: '100%', height: '100%',
      pointerEvents: 'none',
      zIndex: 0,
      opacity: 0.55,
    }} />
  )
}
