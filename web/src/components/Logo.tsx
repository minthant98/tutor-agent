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
  return (
    <svg
      height={height}
      viewBox="0 0 100 140"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className="shrink-0"
    >
      {/* TOP EMERALD — horizontal bar with the right end folded back diagonally */}
      <path d="M 8 14 L 70 14 L 54 54 L 8 54 Z" fill="var(--blue)" />
      {/* BOTTOM NAVY — diagonal stem coming off the emerald, opening into the bottom bar
          which mirrors the emerald (left end folded back diagonally) */}
      <path d="M 54 54 L 70 54 L 92 96 L 92 128 L 36 128 L 54 90 Z" fill="var(--navy)" />
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
      <StrideMark px={s.mark} />
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
