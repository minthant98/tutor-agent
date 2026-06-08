'use client'
import { useId } from 'react'
import Link from 'next/link'

type Size = 'sm' | 'md' | 'lg' | 'xl'

const SIZES: Record<Size, { mark: number; text: string; gap: string }> = {
  sm: { mark: 22, text: 'text-sm',  gap: 'gap-2' },
  md: { mark: 30, text: 'text-xl',  gap: 'gap-2.5' },
  lg: { mark: 40, text: 'text-2xl', gap: 'gap-3' },
  xl: { mark: 72, text: 'text-5xl', gap: 'gap-4' },
}

type Props = {
  size?: Size
  showTagline?: boolean
  className?: string
  href?: string
}

function StrideMark({ height }: { height: number }) {
  // useId-based IDs so multiple Logo instances on the same page
  // don't collide on gradient defs
  const raw = useId().replace(/:/g, '')
  const emeraldGrad = `${raw}-e`
  const navyGrad = `${raw}-n`

  return (
    <svg
      height={height}
      viewBox="0 0 100 140"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className="shrink-0"
    >
      <defs>
        {/* Emerald ribbon gradient — lighter top-left → darker bottom-right (suggests light from upper-left) */}
        <linearGradient id={emeraldGrad} x1="10%" y1="10%" x2="90%" y2="90%">
          <stop offset="0%" stopColor="#34D399" />
          <stop offset="60%" stopColor="#10B981" />
          <stop offset="100%" stopColor="#047857" />
        </linearGradient>
        {/* Navy ribbon gradient — lighter top-right → darker bottom-left (mirrored light direction) */}
        <linearGradient id={navyGrad} x1="100%" y1="10%" x2="20%" y2="100%">
          <stop offset="0%" stopColor="#334155" />
          <stop offset="60%" stopColor="#1E293B" />
          <stop offset="100%" stopColor="#0F172A" />
        </linearGradient>
      </defs>

      {/* TOP EMERALD — main ribbon face */}
      <path
        d="M 8 14 L 70 14 L 54 54 L 8 54 Z"
        fill={`url(#${emeraldGrad})`}
      />
      {/* TOP EMERALD — fold highlight: a brighter wedge along the diagonal cut,
          suggesting where the inside of the ribbon catches light at the crease */}
      <path
        d="M 70 14 L 54 54 L 62 34 L 66 22 Z"
        fill="#6EE7B7"
        opacity="0.55"
      />
      {/* TOP EMERALD — crease shadow: a thin dark line right at the fold edge */}
      <path
        d="M 70 14 L 54 54 L 50 50 L 66 14 Z"
        fill="#065F46"
        opacity="0.35"
      />

      {/* BOTTOM NAVY — main ribbon face (J-shape: diagonal stem + bottom bar) */}
      <path
        d="M 54 54 L 70 54 L 92 96 L 92 128 L 36 128 L 54 90 Z"
        fill={`url(#${navyGrad})`}
      />
      {/* BOTTOM NAVY — fold highlight on the bottom-left crease (mirrors the emerald fold) */}
      <path
        d="M 36 128 L 54 90 L 50 110 L 44 122 Z"
        fill="#475569"
        opacity="0.55"
      />
      {/* BOTTOM NAVY — crease shadow */}
      <path
        d="M 36 128 L 54 90 L 58 94 L 40 128 Z"
        fill="#020617"
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
