import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import client from '@/api/client'
import { useWebSocket } from '@/hooks/useWebSocket'
import Navbar from '@/components/Navbar'
import AgentProgress from '@/components/AgentProgress'
import ResumeViewer from '@/components/ResumeViewer'
import ReactMarkdown from 'react-markdown'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import {
  ArrowLeft,
  Copy,
  Check,
  FileText,
  FileCode,
  Mail,
  Building2,
  Sparkles,
  ChevronDown,
  HelpCircle,
  ExternalLink,
} from 'lucide-react'

const STATUS_CONFIG = [
  { id: 'saved', label: 'Saved', color: 'bg-slate-500 text-white' },
  { id: 'applied', label: 'Applied', color: 'bg-blue-600 text-white' },
  { id: 'interview', label: 'Interview', color: 'bg-amber-600 text-white' },
  { id: 'offer', label: 'Offer', color: 'bg-emerald-600 text-white' },
  { id: 'rejected', label: 'Rejected', color: 'bg-rose-600 text-white' },
]

function InterviewQuestions({ questions }) {
  const [openHints, setOpenHints] = useState({})
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

  function toggleHint(key) {
    setOpenHints((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  return (
    <div className="space-y-6">
      {Object.entries(grouped).map(([category, items]) => (
        <div key={category} className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-primary" />
            <h3 className="font-semibold text-sm uppercase tracking-wider text-muted-foreground">
              {category.replace(/_/g, ' ')} Questions
            </h3>
          </div>

          <div className="space-y-3">
            {(Array.isArray(items) ? items : []).map((q, i) => {
              const question = typeof q === 'string' ? q : q.question
              const hint = typeof q === 'object' ? q.hint : null
              const key = `${category}-${i}`
              const isHintOpen = !!openHints[key]

              return (
                <div
                  key={i}
                  className="rounded-2xl border border-border/70 bg-card p-4 transition-all duration-200 hover:border-primary/30 space-y-2 shadow-xs"
                >
                  <div className="flex items-start gap-3">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary text-xs font-semibold">
                      {i + 1}
                    </span>
                    <p className="font-medium text-sm text-foreground pt-0.5 leading-relaxed">{question}</p>
                  </div>

                  {hint && (
                    <div className="pl-9 pt-1">
                      <button
                        onClick={() => toggleHint(key)}
                        className="inline-flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary/80 transition-colors cursor-pointer"
                      >
                        <HelpCircle className="h-3.5 w-3.5" />
                        <span>{isHintOpen ? 'Hide recommended answer tips' : 'Show answer strategy & hints'}</span>
                        <ChevronDown className={`h-3 w-3 transition-transform ${isHintOpen ? 'rotate-180' : ''}`} />
                      </button>

                      {isHintOpen && (
                        <div className="mt-2 rounded-xl bg-muted/50 border border-border/60 p-3 text-xs text-muted-foreground leading-relaxed animate-in fade-in-50">
                          <p className="font-semibold text-foreground mb-1 text-[11px] uppercase tracking-wider">
                            💡 Coaching Tip:
                          </p>
                          {hint}
                        </div>
                      )}
                    </div>
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
    <Button variant="outline" size="sm" onClick={copy} className="rounded-xl gap-1.5 h-8 text-xs">
      {copied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
      {copied ? 'Copied to Clipboard' : 'Copy Text'}
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
    client
      .get(`/jobs/${id}`)
      .then(({ data }) => setApp(data))
      .finally(() => setLoading(false))
  }, [id])

  // Refresh app data when pipeline completes via WS
  useEffect(() => {
    const last = messages[messages.length - 1]
    if (!last) return
    if (last.type === 'sync' && last.pipeline_status === 'completed') {
      client.get(`/jobs/${id}`).then(({ data }) => setApp(data))
      return
    }
    if (
      last?.pipeline_status === 'completed' ||
      (last?.status === 'completed' && last?.agent === 'synthesizer')
    ) {
      client.get(`/jobs/${id}`).then(({ data }) => setApp(data))
    }
  }, [messages, id])

  async function updateStatus(status) {
    await client.patch(`/jobs/${id}/status`, { status })
    setApp((prev) => ({ ...prev, status }))
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6">
          <Skeleton className="h-8 w-48 rounded-xl" />
          <Skeleton className="h-32 w-full rounded-2xl" />
          <Skeleton className="h-96 w-full rounded-2xl" />
        </div>
      </div>
    )
  }

  if (!app) return null

  const pipelineDone = app.pipeline_status === 'completed'
  const companyInitial = app.company ? app.company.charAt(0).toUpperCase() : '?'

  return (
    <div className="min-h-screen bg-background text-foreground pb-20">
      <Navbar />

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-8">
        {/* Navigation Breadcrumb & Back */}
        <div className="flex items-center justify-between">
          <Button
            variant="ghost"
            size="sm"
            className="rounded-xl gap-1.5 text-muted-foreground hover:text-foreground"
            onClick={() => navigate('/dashboard')}
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Dashboard</span>
          </Button>

          {app.jd_url && (
            <a
              href={app.jd_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <span>View Original Job Posting</span>
              <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>

        {/* Header Hero Card */}
        <div className="rounded-2xl border border-border/70 bg-card p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="h-14 w-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center font-bold text-primary text-2xl shadow-xs">
              {companyInitial}
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">{app.company}</h1>
              <p className="text-base text-muted-foreground mt-0.5">{app.role}</p>
            </div>
          </div>

          {/* Status Stepper / Switcher */}
          <div className="flex flex-col gap-1.5 sm:items-end">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Application Stage
            </span>
            <div className="flex items-center gap-1 bg-muted/50 p-1 rounded-xl border border-border/60">
              {STATUS_CONFIG.map((s) => {
                const isActive = app.status === s.id
                return (
                  <button
                    key={s.id}
                    onClick={() => updateStatus(s.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                      isActive
                        ? `${s.color} shadow-xs font-semibold`
                        : 'text-muted-foreground hover:text-foreground hover:bg-background/80'
                    }`}
                  >
                    {s.label}
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        {/* Pipeline Execution / Agent Progress Card */}
        {!pipelineDone && (
          <Card className="rounded-2xl border-border/70 shadow-xs overflow-hidden">
            <CardHeader className="bg-muted/20 border-b border-border/40 pb-4">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Sparkles className="h-5 w-5 text-amber-500 animate-pulse" />
                AI Analysis & Material Generation Pipeline
              </CardTitle>
              <CardDescription>
                Our multi-agent system is parsing the job description, researching the company, tailoring your resume, and crafting interview strategy in real time.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              <AgentProgress messages={messages} />
            </CardContent>
          </Card>
        )}

        {/* Results Tabs */}
        {pipelineDone && (
          <Tabs defaultValue="jd" className="space-y-6">
            <div className="overflow-x-auto pb-1 scrollbar-none">
              <TabsList className="h-11 p-1 bg-muted/60 rounded-xl border border-border/60 gap-1 w-full justify-start sm:w-auto inline-flex">
                <TabsTrigger value="jd" className="rounded-lg gap-1.5 text-xs sm:text-sm data-[state=active]:shadow-xs">
                  <FileText className="h-4 w-4" /> Parsed JD
                </TabsTrigger>
                <TabsTrigger value="resume" className="rounded-lg gap-1.5 text-xs sm:text-sm data-[state=active]:shadow-xs">
                  <FileCode className="h-4 w-4" /> Tailored Resume
                </TabsTrigger>
                <TabsTrigger value="cover" className="rounded-lg gap-1.5 text-xs sm:text-sm data-[state=active]:shadow-xs">
                  <Mail className="h-4 w-4" /> Cover Letter
                </TabsTrigger>
                <TabsTrigger value="research" className="rounded-lg gap-1.5 text-xs sm:text-sm data-[state=active]:shadow-xs">
                  <Building2 className="h-4 w-4" /> Company Research
                </TabsTrigger>
                <TabsTrigger value="interview" className="rounded-lg gap-1.5 text-xs sm:text-sm data-[state=active]:shadow-xs">
                  <Sparkles className="h-4 w-4" /> Interview Prep
                </TabsTrigger>
              </TabsList>
            </div>

            {/* TAB 1: Parsed JD */}
            <TabsContent value="jd">
              <Card className="rounded-2xl border-border/70 shadow-xs">
                <CardContent className="p-6 space-y-6">
                  {/* Overview Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 rounded-xl bg-muted/30 border border-border/60">
                    <div>
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Company</p>
                      <p className="font-semibold text-sm mt-0.5">{app.parsed_jd?.company_name || app.company}</p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Role Title</p>
                      <p className="font-semibold text-sm mt-0.5">{app.parsed_jd?.role_title || app.role}</p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Experience Level</p>
                      <p className="font-semibold text-sm mt-0.5 capitalize">
                        {app.parsed_jd?.experience_level || 'Not specified'}
                      </p>
                    </div>
                  </div>

                  {/* Required Skills */}
                  {(app.parsed_jd?.required_skills?.length > 0 || app.parsed_jd?.skills?.length > 0) && (
                    <div className="space-y-2.5">
                      <h3 className="font-semibold text-sm text-foreground">Required Skills & Technologies</h3>
                      <div className="flex flex-wrap gap-2">
                        {(app.parsed_jd?.required_skills || app.parsed_jd?.skills || []).map((s) => (
                          <Badge
                            key={s}
                            variant="secondary"
                            className="rounded-lg px-2.5 py-1 text-xs font-medium bg-primary/10 text-primary border-primary/20"
                          >
                            {s}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Nice-to-Have Skills */}
                  {app.parsed_jd?.nice_to_have_skills?.length > 0 && (
                    <div className="space-y-2.5">
                      <h3 className="font-semibold text-sm text-muted-foreground">Nice-to-Have Skills</h3>
                      <div className="flex flex-wrap gap-2">
                        {app.parsed_jd.nice_to_have_skills.map((s) => (
                          <Badge key={s} variant="outline" className="rounded-lg px-2.5 py-1 text-xs">
                            {s}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Key Responsibilities */}
                  {(app.parsed_jd?.key_responsibilities?.length > 0 || app.parsed_jd?.requirements?.length > 0) && (
                    <div className="space-y-3">
                      <h3 className="font-semibold text-sm text-foreground">Key Responsibilities & Requirements</h3>
                      <ul className="space-y-2 text-sm text-muted-foreground leading-relaxed">
                        {(app.parsed_jd?.key_responsibilities || app.parsed_jd?.requirements || []).map((r, i) => (
                          <li key={i} className="flex items-start gap-2.5">
                            <span className="h-1.5 w-1.5 rounded-full bg-primary mt-2 shrink-0" />
                            <span>{r}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* TAB 2: Tailored Resume */}
            <TabsContent value="resume">
              <Card className="rounded-2xl border-border/70 shadow-xs">
                <CardHeader className="pb-3 border-b border-border/40">
                  <CardTitle className="text-base font-semibold">Tailored LaTeX Resume</CardTitle>
                  <CardDescription>
                    Customized to emphasize keywords and achievements aligned with this specific job description.
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-6">
                  <ResumeViewer latexString={app.tailored_resume_latex || app.tailored_resume} />
                </CardContent>
              </Card>
            </TabsContent>

            {/* TAB 3: Cover Letter */}
            <TabsContent value="cover">
              <Card className="rounded-2xl border-border/70 shadow-xs">
                <CardHeader className="pb-3 border-b border-border/40 flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-semibold">Tailored Cover Letter</CardTitle>
                    <CardDescription>
                      AI-generated cover letter highlighting your relevant experience for {app.company}.
                    </CardDescription>
                  </div>
                  {app.cover_letter && <CopyButton text={app.cover_letter} />}
                </CardHeader>
                <CardContent className="p-6">
                  <div className="rounded-xl bg-muted/20 border border-border/60 p-6 text-sm leading-relaxed whitespace-pre-wrap font-sans text-foreground">
                    {app.cover_letter || 'No cover letter generated.'}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* TAB 4: Company Research */}
            <TabsContent value="research">
              <Card className="rounded-2xl border-border/70 shadow-xs">
                <CardHeader className="pb-3 border-b border-border/40">
                  <CardTitle className="text-base font-semibold">Company Dossier & Strategic Intel</CardTitle>
                  <CardDescription>
                    Key insights into business model, recent news, engineering culture, and strategic priorities.
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="prose prose-sm dark:prose-invert max-w-none space-y-3 leading-relaxed [&_h1]:text-lg [&_h1]:font-bold [&_h1]:mt-4 [&_h1]:mb-2 [&_h2]:text-base [&_h2]:font-semibold [&_h2]:mt-3 [&_h2]:mb-1 [&_h3]:text-sm [&_h3]:font-semibold [&_ul]:list-disc [&_ul]:list-inside [&_ol]:list-decimal [&_ol]:list-inside [&_p]:mb-2 [&_strong]:font-semibold text-muted-foreground">
                    <ReactMarkdown>{app.company_research}</ReactMarkdown>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* TAB 5: Interview Prep */}
            <TabsContent value="interview">
              <Card className="rounded-2xl border-border/70 shadow-xs">
                <CardHeader className="pb-3 border-b border-border/40">
                  <CardTitle className="text-base font-semibold">Interview Questions & Preparation Kit</CardTitle>
                  <CardDescription>
                    Curated technical, behavioral, and architectural questions tailored to this role with answering strategies.
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-6">
                  <InterviewQuestions questions={app.interview_questions} />
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        )}
      </main>
    </div>
  )
}
