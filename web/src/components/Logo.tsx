'use client'
import { useId } from 'react'
import Link from 'next/link'

type Size = 'sm' | 'md' | 'lg' | 'xl'

const SIZES: Record<Size, { mark: number; text: string; gap: string }> = {
  sm: { mark: 26, text: 'text-sm',  gap: 'gap-2' },
  md: { mark: 36, text: 'text-xl',  gap: 'gap-2.5' },
  lg: { mark: 48, text: 'text-2xl', gap: 'gap-3' },
  xl: { mark: 88, text: 'text-5xl', gap: 'gap-4' },
}

type Props = {
  size?: Size
  showTagline?: boolean
  className?: string
  href?: string
}

function StrideMark({ height }: { height: number }) {
  // useId-based gradient ids so multiple <Logo>s on the same page don't collide
  const raw = useId().replace(/:/g, '')
  const emeraldGrad = `${raw}-e`
  const navyGrad = `${raw}-n`

  return (
    <svg
      height={height}
      viewBox="0 0 100 100"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className="shrink-0"
    >
      <defs>
        {/* Emerald — light upper-left → dark lower-right */}
        <linearGradient id={emeraldGrad} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%"   stopColor="#5EEAD4" />
          <stop offset="55%"  stopColor="#10B981" />
          <stop offset="100%" stopColor="#047857" />
        </linearGradient>
        {/* Navy — light upper-right → dark lower-left (mirrored) */}
        <linearGradient id={navyGrad} x1="100%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%"   stopColor="#3B5278" />
          <stop offset="55%"  stopColor="#1E293B" />
          <stop offset="100%" stopColor="#0A1027" />
        </linearGradient>
      </defs>

      {/*
        TOP EMERALD — horizontal bar at the top:
        - rounded top-left (r=16)
        - flat top, short right-edge drop (20 units)
        - 45° diagonal cut from (80,20) down to (50,50) — the upper edge
          of the S's crossbar
        - flat bottom (50,50) → (0,50)
        - flat left edge up to the rounded corner
      */}
      <path
        d="M 16 0 L 80 0 L 80 20 L 50 50 L 0 50 L 0 16 A 16 16 0 0 1 16 0 Z"
        fill={`url(#${emeraldGrad})`}
      />

      {/*
        Fold shadow on the emerald — darker triangle along the diagonal
        suggesting the navy ribbon folds over the top of it
      */}
      <path
        d="M 80 20 L 50 50 L 25 50 Z"
        fill="#064E3B"
        opacity="0.45"
      />

      {/*
        BOTTOM NAVY — horizontal bar at the bottom, mirror of the emerald:
        - 45° diagonal cut from (50,50) down to (20,80) — lower edge of
          the crossbar; continues the same straight line as the emerald's
          diagonal (both have slope -1 through (50,50))
        - flat left edge down to bottom
        - rounded bottom-right (r=16)
        - flat top edge back to the diagonal start
      */}
      <path
        d="M 50 50 L 100 50 L 100 84 A 16 16 0 0 1 84 100 L 20 100 L 20 80 L 50 50 Z"
        fill={`url(#${navyGrad})`}
      />

      {/*
        Subtle highlight on the navy at its diagonal edge — hint of light
        catching the top of the bottom fold
      */}
      <path
        d="M 50 50 L 20 80 L 20 70 L 40 50 Z"
        fill="#475569"
        opacity="0.30"
      />
    </svg>
  )
}

export default function Logo({
  size = 'md',
  showTagline = false,
  className = '',
  href,
}: Props) {
  const s = SIZES[size]
  const content = (
    <div className={`inline-flex items-center ${s.gap} ${className}`}>
      <StrideMark height={s.mark} />
      <div className="flex flex-col leading-none">
        <span className={`font-bold tracking-tight ${s.text}`} style={{ color: 'var(--navy)' }}>
          Stride
        </span>
        {showTagline && (
          <span className="text-[11px] font-medium mt-1.5 tracking-wide" style={{ color: 'var(--text-secondary)' }}>
            Your AI Learning Companion
          </span>
        )}
      </div>
    </div>
  )
  return href ? <Link href={href} className="inline-block">{content}</Link> : content
}
