import { useState } from 'react'

export default function Card({ children, style, className, glow, topBorder, onClick }) {
  const [hovered, setHovered] = useState(false)

  return (
    <div
      className={className}
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered
          ? 'rgba(255,255,255,0.055)'
          : 'rgba(255,255,255,0.028)',
        border: `1px solid ${hovered
          ? 'rgba(130,100,255,0.40)'
          : 'rgba(255,255,255,0.09)'}`,
        borderTop: topBorder
          ? `1px solid ${topBorder}`
          : undefined,
        borderRadius: '18px',
        backdropFilter: 'blur(28px)',
        WebkitBackdropFilter: 'blur(28px)',
        boxShadow: hovered
          ? '0 8px 48px rgba(100,60,255,0.18), inset 0 1px 0 rgba(255,255,255,0.1)'
          : '0 4px 32px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.05)',
        transition: 'all 0.3s cubic-bezier(0.4,0,0.2,1)',
        ...style
      }}
    >
      {children}
    </div>
  )
}
