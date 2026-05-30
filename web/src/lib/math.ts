import katex from 'katex'

function renderKatex(tex: string, displayMode: boolean): string {
  try {
    return katex.renderToString(tex, { displayMode, throwOnError: false, output: 'html' })
  } catch {
    return tex
  }
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')
}

export function renderMath(text: string): string {
  const parts: string[] = []
  // Split on $$...$$ or $...$ (display math first to avoid double-matching)
  const pattern = /(\$\$[\s\S]+?\$\$|\$[^$\n]+?\$)/g
  let last = 0
  let m: RegExpExecArray | null

  while ((m = pattern.exec(text)) !== null) {
    // Text segment before match
    if (m.index > last) {
      parts.push(escapeHtml(text.slice(last, m.index)))
    }
    const raw = m[0]
    if (raw.startsWith('$$')) {
      parts.push(renderKatex(raw.slice(2, -2).trim(), true))
    } else {
      parts.push(renderKatex(raw.slice(1, -1).trim(), false))
    }
    last = m.index + raw.length
  }

  // Remaining text
  if (last < text.length) {
    parts.push(escapeHtml(text.slice(last)))
  }

  return parts.join('')
}
