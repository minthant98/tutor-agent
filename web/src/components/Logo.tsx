import Link from 'next/link'

type Size = 'sm' | 'md' | 'lg' | 'xl'

const SIZES: Record<Size, { mark: number; text: string; gap: string }> = {
  sm: { mark: 18, text: 'text-sm',  gap: 'gap-2' },
  md: { mark: 24, text: 'text-xl',  gap: 'gap-2.5' },
  lg: { mark: 32, text: 'text-2xl', gap: 'gap-3' },
  xl: { mark: 56, text: 'text-5xl', gap: 'gap-4' },
}

type Props = {
  size?: Size
  showTagline?: boolean
  className?: string
  href?: string
}

function StrideMark({ px }: { px: number }) {
  return (
    <svg
      width={px}
      height={px}
      viewBox="0 0 32 32"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className="shrink-0"
    >
      {/* Top: emerald — parallelogram leaning right */}
      <path d="M4 4 L22 4 L26 16 L8 16 Z" fill="var(--blue)" />
      {/* Bottom: navy — parallelogram leaning left, completing the S */}
      <path d="M8 16 L26 16 L22 28 L4 28 Z" fill="var(--navy)" />
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
