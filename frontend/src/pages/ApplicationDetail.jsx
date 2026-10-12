import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import client from '@/api/client'
import { useWebSocket } from '@/hooks/useWebSocket'
import Navbar from '@/components/Navbar'
import AgentProgress from '@/components/AgentProgress'
import ResumeViewer from '@/components/ResumeViewer'
import ReactMarkdown from 'react-markdown'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import { ArrowLeft, Copy, Check } from 'lucide-react'

const STATUSES = ['saved', 'applied', 'interview', 'offer', 'rejected']

function InterviewQuestions({ questions }) {
  const [open, setOpen] = useState({})
  if (!questions) return null

  // Normalize questions whether provided as array or object
  const grouped = {}
  if (Array.isArray(questions)) {
    questions.forEach((q) => {
      const cat = q.category || 'general'
      if (!grouped[cat]) grouped[cat] = []
      grouped[cat].push(q)
    })
  } else if (typeof questions === 'object') {
    Object.assign(grouped, questions)
  }

  return (
    <div className="space-y-6">
      {Object.entries(grouped).map(([category, items]) => (
        <div key={category}>
          <h3 className="font-semibold capitalize mb-2">{category.replace(/_/g, ' ')}</h3>
          <div className="space-y-2">
            {(Array.isArray(items) ? items : []).map((q, i) => {
              const question = typeof q === 'string' ? q : q.question
              const hint = typeof q === 'object' ? q.hint : null
              return (
                <div key={i} className="rounded border p-3 text-sm">
                  <p className="font-medium">{question}</p>
                  {hint && (
                    <button
                      className="text-xs text-muted-foreground mt-2 underline cursor-pointer block"
                      onClick={() => setOpen((prev) => ({ ...prev, [`${category}-${i}`]: !prev[`${category}-${i}`] }))}
                    >
                      {open[`${category}-${i}`] ? 'Hide hint' : 'Show hint'}
                    </button>
                  )}
                  {open[`${category}-${i}`] && hint && (
                    <p className="text-xs text-muted-foreground mt-1 bg-muted/40 p-2 rounded">{hint}</p>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  function copy() {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <Button variant="outline" size="sm" onClick={copy}>
      {copied ? <Check className="h-4 w-4 mr-1" /> : <Copy className="h-4 w-4 mr-1" />}
      {copied ? 'Copied' : 'Copy'}
    </Button>
  )
}

export default function ApplicationDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [app, setApp] = useState(null)
  const [loading, setLoading] = useState(true)
  const { messages } = useWebSocket(app && app.pipeline_status !== 'completed' ? id : null)

  useEffect(() => {
    client.get(`/jobs/${id}`).then(({ data }) => setApp(data)).finally(() => setLoading(false))
  }, [id])

  // Refresh app data when pipeline completes via WS
  useEffect(() => {
    const last = messages[messages.length - 1]
    if (!last) return
    // sync message = WS just connected, pipeline already done
    if (last.type === 'sync' && last.pipeline_status === 'completed') {
      client.get(`/jobs/${id}`).then(({ data }) => setApp(data))
      return
    }
    if (last?.pipeline_status === 'completed' || (last?.status === 'completed' && last?.agent === 'synthesizer')) {
      client.get(`/jobs/${id}`).then(({ data }) => setApp(data))
    }
  }, [messages, id])

  async function updateStatus(status) {
    await client.patch(`/jobs/${id}/status`, { status })
    setApp((prev) => ({ ...prev, status }))
  }

  if (loading) return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="max-w-4xl mx-auto px-6 py-8 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48 w-full" />
      </div>
    </div>
  )

  if (!app) return null

  const pipelineDone = app.pipeline_status === 'completed'

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">

        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <Button variant="ghost" size="sm" className="mb-2 -ml-2" onClick={() => navigate('/dashboard')}>
              <ArrowLeft className="h-4 w-4 mr-1" /> Dashboard
            </Button>
            <h1 className="text-2xl font-bold">{app.company}</h1>
            <p className="text-muted-foreground">{app.role}</p>
          </div>
          <div className="flex gap-2 flex-wrap justify-end">
            {STATUSES.map((s) => (
              <Button
                key={s}
                variant={app.status === s ? 'default' : 'outline'}
                size="sm"
                onClick={() => updateStatus(s)}
              >
                {s}
              </Button>
            ))}
          </div>
        </div>

        {/* Agent Progress */}
        {!pipelineDone && (
          <Card>
            <CardHeader><CardTitle>Agent Progress</CardTitle></CardHeader>
            <CardContent>
              <AgentProgress messages={messages} />
            </CardContent>
          </Card>
        )}

        {/* Results */}
        {pipelineDone && (
          <Tabs defaultValue="jd">
            <TabsList className="flex-wrap h-auto gap-1">
              <TabsTrigger value="jd">Parsed JD</TabsTrigger>
              <TabsTrigger value="resume">Resume</TabsTrigger>
              <TabsTrigger value="cover">Cover Letter</TabsTrigger>
              <TabsTrigger value="research">Company Research</TabsTrigger>
              <TabsTrigger value="interview">Interview Prep</TabsTrigger>
            </TabsList>

            <TabsContent value="jd">
              <Card><CardContent className="p-4 space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 border-b pb-4">
                  <div>
                    <p className="text-xs text-muted-foreground">Company</p>
                    <p className="font-semibold text-sm">{app.parsed_jd?.company_name || app.company}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Role</p>
                    <p className="font-semibold text-sm">{app.parsed_jd?.role_title || app.role}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Experience Level</p>
                    <p className="font-semibold text-sm capitalize">{app.parsed_jd?.experience_level || 'Not specified'}</p>
                  </div>
                </div>

                {((app.parsed_jd?.required_skills?.length > 0) || (app.parsed_jd?.skills?.length > 0)) && (
                  <div>
                    <p className="font-semibold mb-2">Required Skills</p>
                    <div className="flex flex-wrap gap-2">
                      {(app.parsed_jd?.required_skills || app.parsed_jd?.skills || []).map((s) => (
                        <Badge key={s} variant="secondary">{s}</Badge>
                      ))}
                    </div>
                  </div>
                )}

                {app.parsed_jd?.nice_to_have_skills?.length > 0 && (
                  <div>
                    <p className="font-semibold mb-2">Nice-to-Have Skills</p>
                    <div className="flex flex-wrap gap-2">
                      {app.parsed_jd.nice_to_have_skills.map((s) => (
                        <Badge key={s} variant="outline">{s}</Badge>
                      ))}
                    </div>
                  </div>
                )}

                {((app.parsed_jd?.key_responsibilities?.length > 0) || (app.parsed_jd?.requirements?.length > 0)) && (
                  <div>
                    <p className="font-semibold mb-2">Key Responsibilities & Requirements</p>
                    <ul className="list-disc list-inside space-y-1 text-sm">
                      {(app.parsed_jd?.key_responsibilities || app.parsed_jd?.requirements || []).map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent></Card>
            </TabsContent>

            <TabsContent value="resume">
              <Card><CardContent className="p-4">
                <ResumeViewer latexString={app.tailored_resume_latex || app.tailored_resume} />
              </CardContent></Card>
            </TabsContent>

            <TabsContent value="cover">
              <Card><CardContent className="p-4 space-y-3">
                {app.cover_letter && <CopyButton text={app.cover_letter} />}
                <p className="text-sm whitespace-pre-wrap">{app.cover_letter}</p>
              </CardContent></Card>
            </TabsContent>

            <TabsContent value="research">
              <Card><CardContent className="p-4">
                <div className="text-sm space-y-2 [&_h1]:text-lg [&_h1]:font-bold [&_h1]:mt-4 [&_h1]:mb-2 [&_h2]:text-base [&_h2]:font-semibold [&_h2]:mt-3 [&_h2]:mb-1 [&_h3]:text-sm [&_h3]:font-semibold [&_ul]:list-disc [&_ul]:list-inside [&_ol]:list-decimal [&_ol]:list-inside [&_p]:mb-2 [&_strong]:font-semibold">
                  <ReactMarkdown>{app.company_research}</ReactMarkdown>
                </div>
              </CardContent></Card>
            </TabsContent>

            <TabsContent value="interview">
              <Card><CardContent className="p-4">
                <InterviewQuestions questions={app.interview_questions} />
              </CardContent></Card>
            </TabsContent>
          </Tabs>
        )}
      </div>
    </div>
  )
}
