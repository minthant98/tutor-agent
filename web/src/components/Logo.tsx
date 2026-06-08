'use client'
import { useId } from 'react'
import Link from 'next/link'

type Size = 'sm' | 'md' | 'lg' | 'xl'

const SIZES: Record<Size, { mark: number; text: string; gap: string }> = {
  sm: { mark: 24, text: 'text-sm',  gap: 'gap-2' },
  md: { mark: 32, text: 'text-xl',  gap: 'gap-2.5' },
  lg: { mark: 44, text: 'text-2xl', gap: 'gap-3' },
  xl: { mark: 80, text: 'text-5xl', gap: 'gap-4' },
}

type Props = {
  size?: Size
  showTagline?: boolean
  className?: string
  href?: string
}

function StrideMark({ height }: { height: number }) {
  // useId-based gradient ids so multiple <Logo>s on a page don't collide
  const raw = useId().replace(/:/g, '')
  const emeraldGrad = `${raw}-e`
  const navyGrad = `${raw}-n`

  return (
    <svg
      height={height}
      viewBox="0 0 100 110"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className="shrink-0"
    >
      <defs>
        {/* Emerald — light at upper-left → dark at lower-right (light source from upper-left) */}
        <linearGradient id={emeraldGrad} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%"  stopColor="#5EEAD4" />
          <stop offset="55%" stopColor="#10B981" />
          <stop offset="100%" stopColor="#047857" />
        </linearGradient>
        {/* Navy — light at upper-right → dark at lower-left (mirrored light direction) */}
        <linearGradient id={navyGrad} x1="100%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%"  stopColor="#3B5278" />
          <stop offset="55%" stopColor="#1E293B" />
          <stop offset="100%" stopColor="#0A1027" />
        </linearGradient>
      </defs>

      {/*
        TOP EMERALD — a horizontal bar that is:
        - rounded at the top-left corner (radius 18)
        - has a short vertical right edge dropping down
        - cut diagonally (45°) from upper-right to lower-left
          forming the upper half of the S's crossbar
      */}
      <path
        d="
          M 18 0
          L 70 0
          L 70 35
          L 50 55
          L 0 55
          L 0 18
          A 18 18 0 0 1 18 0
          Z
        "
        fill={`url(#${emeraldGrad})`}
      />

      {/*
        Fold shadow on the emerald — a darker triangle along the diagonal
        cut, suggesting the navy ribbon folds over the top of the emerald
        and casts a shadow on it
      */}
      <path
        d="M 70 35 L 50 55 L 28 55 Z"
        fill="#064E3B"
        opacity="0.42"
      />

      {/*
        BOTTOM NAVY — mirror of the emerald:
        - starts at the end of the emerald's diagonal cut
        - flat top edge, vertical right edge
        - rounded at the bottom-right corner (radius 18)
        - flat bottom edge
        - left edge with diagonal cut at the top-left (mirror of emerald)
      */}
      <path
        d="
          M 50 55
          L 100 55
          L 100 92
          A 18 18 0 0 1 82 110
          L 30 110
          L 30 75
          L 50 55
          Z
        "
        fill={`url(#${navyGrad})`}
      />

      {/*
        Subtle highlight on the navy at the fold edge — where the ribbon
        emerges from beneath the emerald and catches a hint of light
      */}
      <path
        d="M 50 55 L 30 75 L 30 65 L 45 55 Z"
        fill="#475569"
        opacity="0.35"
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
