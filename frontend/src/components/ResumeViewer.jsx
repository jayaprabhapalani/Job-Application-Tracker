import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Download, Copy, Check } from 'lucide-react'

export default function ResumeViewer({ latexString }) {
  const [copied, setCopied] = useState(false)

  if (!latexString) return null

  function handleDownload() {
    const blob = new Blob([latexString], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'resume.tex'
    a.click()
    URL.revokeObjectURL(url)
  }

  function handleCopy() {
    navigator.clipboard.writeText(latexString)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={handleDownload}>
          <Download className="h-4 w-4 mr-1" /> Download .tex
        </Button>
        <Button variant="outline" size="sm" onClick={handleCopy}>
          {copied ? <Check className="h-4 w-4 mr-1" /> : <Copy className="h-4 w-4 mr-1" />}
          {copied ? 'Copied' : 'Copy'}
        </Button>
        <span className="text-xs text-muted-foreground ml-2">
          Paste into <a href="https://www.overleaf.com" target="_blank" rel="noreferrer" className="underline">Overleaf</a> to compile to PDF
        </span>
      </div>
      <pre className="rounded border p-4 text-xs overflow-auto max-h-[600px] bg-muted/20 whitespace-pre-wrap font-mono">
        {latexString}
      </pre>
    </div>
  )
}
