import { useRef } from 'react'
import Latex from 'react-latex-next'
import { Button } from '@/components/ui/button'
import { Download, Printer } from 'lucide-react'
import 'katex/dist/katex.min.css'

export default function ResumeViewer({ latexString }) {
  const viewerRef = useRef(null)

  function handleDownload() {
    const blob = new Blob([latexString], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'resume.tex'
    a.click()
    URL.revokeObjectURL(url)
  }

  function handlePrint() {
    const content = viewerRef.current?.innerHTML
    const win = window.open('', '_blank')
    win.document.write(`<html><body>${content}</body></html>`)
    win.document.close()
    win.print()
  }

  if (!latexString) return null

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={handleDownload}>
          <Download className="h-4 w-4 mr-1" /> Download .tex
        </Button>
        <Button variant="outline" size="sm" onClick={handlePrint}>
          <Printer className="h-4 w-4 mr-1" /> Print
        </Button>
      </div>
      <div ref={viewerRef} className="rounded border p-4 font-mono text-sm overflow-auto max-h-[600px]">
        <Latex>{latexString}</Latex>
      </div>
    </div>
  )
}
