import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '@/api/client'
import Navbar from '@/components/Navbar'
import ApplicationCard from '@/components/ApplicationCard'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Plus,
  FileText,
  Search,
  Briefcase,
  Send,
  CalendarCheck,
  Trophy,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Bookmark,
  XCircle,
  LayoutGrid,
  UploadCloud,
  FileCheck,
} from 'lucide-react'

const STATUS_FILTERS = [
  { id: 'all', label: 'All', icon: LayoutGrid, iconColor: 'text-slate-500' },
  { id: 'saved', label: 'Saved', icon: Bookmark, iconColor: 'text-slate-500' },
  { id: 'applied', label: 'Applied', icon: Send, iconColor: 'text-blue-500' },
  { id: 'interview', label: 'Interview', icon: CalendarCheck, iconColor: 'text-amber-500' },
  { id: 'offer', label: 'Offer', icon: Trophy, iconColor: 'text-emerald-500' },
  { id: 'rejected', label: 'Rejected', icon: XCircle, iconColor: 'text-rose-500' },
]

export default function Dashboard() {
  const navigate = useNavigate()
  const [applications, setApplications] = useState([])
  const [loadingApps, setLoadingApps] = useState(true)

  // Overlay modal states
  const [isNewAppOpen, setIsNewAppOpen] = useState(false)
  const [isResumeOpen, setIsResumeOpen] = useState(false)

  // Search & filter
  const [searchQuery, setSearchQuery] = useState('')
  const [activeFilter, setActiveFilter] = useState('all')

  // New Application form state
  const [submitting, setSubmitting] = useState(false)
  const [appError, setAppError] = useState('')

  // Resume state
  const [resume, setResume] = useState(null)
  const [resumeSubmitting, setResumeSubmitting] = useState(false)
  const [resumeMsg, setResumeMsg] = useState('')
  const [resumeMsgType, setResumeMsgType] = useState('info')
  const [selectedFileName, setSelectedFileName] = useState('')

  useEffect(() => {
    client
      .get('/jobs/')
      .then(({ data }) => setApplications(data))
      .finally(() => setLoadingApps(false))

    client
      .get('/jobs/resume')
      .then(({ data }) => setResume(data))
      .catch(() => {})
  }, [])

  // KPI counts
  const stats = useMemo(() => {
    return {
      total: applications.length,
      applied: applications.filter((a) => a.status === 'applied').length,
      interviews: applications.filter((a) => a.status === 'interview').length,
      offers: applications.filter((a) => a.status === 'offer').length,
    }
  }, [applications])

  // Filtered applications
  const filteredApplications = useMemo(() => {
    return applications.filter((app) => {
      const matchesStatus = activeFilter === 'all' || app.status === activeFilter
      const query = searchQuery.toLowerCase().trim()
      const matchesSearch =
        !query ||
        app.company?.toLowerCase().includes(query) ||
        app.role?.toLowerCase().includes(query)
      return matchesStatus && matchesSearch
    })
  }, [applications, activeFilter, searchQuery])

  // Handle Resume Submit
  async function handleResumeSubmit(e) {
    e.preventDefault()
    setResumeMsg('')
    setResumeSubmitting(true)
    const raw = new FormData(e.target)
    const file = raw.get('resume_file')
    const content = raw.get('resume_content')
    const form = new FormData()

    if (file && file.size > 0) {
      form.append('file', file)
    } else if (content && content.trim()) {
      form.append('content', content)
    } else {
      setResumeMsg('Provide a file or paste resume text.')
      setResumeMsgType('error')
      setResumeSubmitting(false)
      return
    }

    try {
      const { data } = await client.post('/jobs/resume', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResume(data)
      setResumeMsg('Resume saved and vectorized successfully!')
      setResumeMsgType('success')
      setSelectedFileName('')
      e.target.reset()
    } catch (err) {
      setResumeMsg(err.response?.data?.detail || 'Failed to save resume')
      setResumeMsgType('error')
    } finally {
      setResumeSubmitting(false)
    }
  }

  // Handle New Application Submit
  async function handleNewAppSubmit(e) {
    e.preventDefault()
    setAppError('')
    setSubmitting(true)
    const form = new FormData(e.target)
    try {
      const { data } = await client.post('/jobs/', {
        company: form.get('company'),
        role: form.get('role'),
        jd_text: form.get('jd_text') || ' ',
        jd_url: form.get('jd_url') || undefined,
      })
      setIsNewAppOpen(false)
      navigate(`/applications/${data.id}`)
    } catch (err) {
      setAppError(err.response?.data?.detail || 'Failed to create application')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground pb-20">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 space-y-8">
        {/* Top Header & Action Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-border/60">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">Job Applications</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Track your applications and generate AI-powered interview prep & tailored resumes.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            {/* Active Resume Modal Trigger */}
            <Button
              variant="outline"
              onClick={() => setIsResumeOpen(true)}
              className="gap-2 rounded-xl transition-all cursor-pointer"
            >
              <FileText className="h-4 w-4 text-blue-500" />
              <span>Resume</span>
              {resume && (
                <span className="flex h-2 w-2 rounded-full bg-emerald-500" title="Resume uploaded" />
              )}
            </Button>

            {/* New Application Modal Trigger */}
            <Button
              onClick={() => setIsNewAppOpen(true)}
              className="gap-2 rounded-xl shadow-xs transition-all cursor-pointer"
            >
              <Plus className="h-4 w-4" />
              <span>Add Application</span>
            </Button>
          </div>
        </div>

        {/* Clean Neutral Stat Cards with Colorful Relevant Icons */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="rounded-xl border-border bg-card">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold text-card-foreground">{stats.total}</p>
                <p className="text-xs text-muted-foreground uppercase tracking-wider mt-0.5">Total</p>
              </div>
              <div className="h-9 w-9 rounded-lg border border-border bg-muted/30 flex items-center justify-center">
                <Briefcase className="h-4 w-4 text-indigo-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-xl border-border bg-card">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold text-card-foreground">{stats.applied}</p>
                <p className="text-xs text-muted-foreground uppercase tracking-wider mt-0.5">Applied</p>
              </div>
              <div className="h-9 w-9 rounded-lg border border-border bg-muted/30 flex items-center justify-center">
                <Send className="h-4 w-4 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-xl border-border bg-card">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold text-card-foreground">{stats.interviews}</p>
                <p className="text-xs text-muted-foreground uppercase tracking-wider mt-0.5">Interviews</p>
              </div>
              <div className="h-9 w-9 rounded-lg border border-border bg-muted/30 flex items-center justify-center">
                <CalendarCheck className="h-4 w-4 text-amber-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-xl border-border bg-card">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold text-card-foreground">{stats.offers}</p>
                <p className="text-xs text-muted-foreground uppercase tracking-wider mt-0.5">Offers</p>
              </div>
              <div className="h-9 w-9 rounded-lg border border-border bg-muted/30 flex items-center justify-center">
                <Trophy className="h-4 w-4 text-emerald-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filter Tabs & Search Bar */}
        <div className="space-y-4">
          <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
            {/* Status Pills with Clean Colorful Icons */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0 scrollbar-none">
              {STATUS_FILTERS.map((tab) => {
                const isActive = activeFilter === tab.id
                const IconComponent = tab.icon
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveFilter(tab.id)}
                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all cursor-pointer ${
                      isActive
                        ? 'bg-primary text-primary-foreground shadow-xs'
                        : 'bg-background border border-border text-muted-foreground hover:bg-muted/60 hover:text-foreground'
                    }`}
                  >
                    <IconComponent
                      className={`h-3.5 w-3.5 ${isActive ? 'text-primary-foreground' : tab.iconColor}`}
                    />
                    <span>{tab.label}</span>
                  </button>
                )
              })}
            </div>

            {/* Search Input */}
            <div className="relative min-w-[260px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search company or role…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 h-9 rounded-xl bg-background border-input"
              />
            </div>
          </div>

          {/* Applications Grid */}
          {loadingApps ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-32 rounded-xl" />
              ))}
            </div>
          ) : filteredApplications.length === 0 ? (
            <div className="rounded-xl border border-dashed border-border p-12 text-center flex flex-col items-center justify-center gap-3">
              <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center text-muted-foreground">
                <Briefcase className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-base">No applications found</h3>
              <p className="text-xs text-muted-foreground max-w-sm">
                {searchQuery || activeFilter !== 'all'
                  ? 'No applications match your search filter. Try clearing the query.'
                  : 'Start by tracking your first job opportunity.'}
              </p>
              {searchQuery || activeFilter !== 'all' ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSearchQuery('')
                    setActiveFilter('all')
                  }}
                  className="rounded-xl mt-2 cursor-pointer"
                >
                  Clear Filters
                </Button>
              ) : (
                <Button
                  onClick={() => setIsNewAppOpen(true)}
                  size="sm"
                  className="rounded-xl mt-2 gap-1.5 cursor-pointer"
                >
                  <Plus className="h-4 w-4" /> Add Application
                </Button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
              {filteredApplications.map((app) => (
                <ApplicationCard key={app.id} application={app} />
              ))}
            </div>
          )}
        </div>
      </main>

      {/* ====================================================
          MODAL 1: NEW APPLICATION OVERLAY DIALOG (SPACIOUS & CLEAN)
         ==================================================== */}
      <Dialog open={isNewAppOpen} onOpenChange={setIsNewAppOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-xl font-bold">
              <Plus className="h-5 w-5 text-primary" />
              New Job Application
            </DialogTitle>
            <DialogDescription>
              Enter the role details to trigger automated requirements extraction, resume tailoring, and interview prep.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleNewAppSubmit} className="space-y-4 pt-2">
            {appError && (
              <Alert variant="destructive" className="rounded-xl">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{appError}</AlertDescription>
              </Alert>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="company">Company Name</Label>
                <Input
                  id="company"
                  name="company"
                  placeholder="e.g. Google, Stripe, Microsoft"
                  required
                  className="rounded-xl bg-background border-input"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="role">Role / Position</Label>
                <Input
                  id="role"
                  name="role"
                  placeholder="e.g. Full Stack Engineer"
                  required
                  className="rounded-xl bg-background border-input"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="jd_text">Job Description</Label>
              <Textarea
                id="jd_text"
                name="jd_text"
                rows={6}
                placeholder="Paste the requirements, qualifications, and responsibilities directly from the job posting…"
                className="rounded-xl bg-background border-input resize-y leading-relaxed font-sans"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="jd_url" className="flex items-center justify-between">
                <span>Or Job Posting URL</span>
                <span className="text-xs text-muted-foreground font-normal">Optional automated scraper</span>
              </Label>
              <Input
                id="jd_url"
                name="jd_url"
                type="url"
                placeholder="https://jobs.lever.co/company/role-id..."
                className="rounded-xl bg-background border-input"
              />
            </div>

            <DialogFooter className="gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsNewAppOpen(false)}
                className="rounded-xl cursor-pointer"
              >
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="rounded-xl gap-2 cursor-pointer font-medium">
                <Sparkles className="h-4 w-4" />
                <span>{submitting ? 'Creating & Analyzing…' : 'Start Application Analysis'}</span>
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* ====================================================
          MODAL 2: RESUME MANAGEMENT OVERLAY DIALOG (SPACIOUS & CLEAN)
         ==================================================== */}
      <Dialog open={isResumeOpen} onOpenChange={setIsResumeOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-xl font-bold">
              <FileText className="h-5 w-5 text-primary" />
              Active Resume
            </DialogTitle>
            <DialogDescription>
              Your master resume is stored in vector storage and used to tailor your documents and calculate match scores.
            </DialogDescription>
          </DialogHeader>

          {resume && (
            <div className="rounded-xl bg-muted/60 border border-border p-4 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                <div>
                  <p className="font-semibold text-foreground text-sm">Master Resume Loaded</p>
                  <p className="text-muted-foreground mt-0.5">
                    Last updated on {new Date(resume.created_at).toLocaleDateString()} · {resume.content?.length || 0} characters
                  </p>
                </div>
              </div>
            </div>
          )}

          <form onSubmit={handleResumeSubmit} className="space-y-4 pt-1">
            {resumeMsg && (
              <Alert
                variant={resumeMsgType === 'success' ? 'default' : 'destructive'}
                className="rounded-xl"
              >
                {resumeMsgType === 'success' ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                ) : (
                  <AlertCircle className="h-4 w-4" />
                )}
                <AlertDescription>{resumeMsg}</AlertDescription>
              </Alert>
            )}

            {/* Upload File Zone */}
            <div className="space-y-1.5">
              <Label
                htmlFor="resume_file"
                className="text-xs font-semibold uppercase tracking-wider text-muted-foreground"
              >
                Upload Resume Document
              </Label>
              <label
                htmlFor="resume_file"
                className="flex flex-col items-center justify-center p-6 border-2 border-dashed border-border hover:border-blue-500/60 bg-muted/20 hover:bg-muted/40 rounded-2xl cursor-pointer transition-all text-center group"
              >
                <input
                  id="resume_file"
                  name="resume_file"
                  type="file"
                  accept=".pdf,.docx,.txt"
                  className="sr-only"
                  onChange={(e) => {
                    const file = e.target.files?.[0]
                    setSelectedFileName(file ? file.name : '')
                  }}
                />
                {selectedFileName ? (
                  <div className="flex flex-col items-center gap-1.5">
                    <div className="h-10 w-10 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                      <FileCheck className="h-5 w-5" />
                    </div>
                    <span className="text-sm font-semibold text-foreground max-w-xs truncate">
                      {selectedFileName}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      Click to choose a different file
                    </span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-1.5">
                    <div className="h-10 w-10 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center group-hover:scale-105 transition-transform">
                      <UploadCloud className="h-5 w-5" />
                    </div>
                    <span className="text-sm font-semibold text-foreground">
                      Click to choose file or drag and drop
                    </span>
                    <span className="text-xs text-muted-foreground">
                      Supports PDF, DOCX, or TXT
                    </span>
                  </div>
                )}
              </label>
            </div>

            {/* Centered OR Divider */}
            <div className="relative flex items-center justify-center my-4">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-border" />
              </div>
              <span className="relative bg-card px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                OR
              </span>
            </div>

            {/* Plain Text Paste Section */}
            <div className="space-y-1.5">
              <Label
                htmlFor="resume_content"
                className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground"
              >
                <FileText className="h-3.5 w-3.5 text-slate-500" />
                <span>Paste Resume in Plain Text</span>
              </Label>
              <Textarea
                id="resume_content"
                name="resume_content"
                rows={5}
                placeholder="Paste the raw text of your resume here…"
                defaultValue={resume?.content || ''}
                className="rounded-xl bg-background border-input font-sans leading-relaxed resize-y"
              />
            </div>

            <DialogFooter className="gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsResumeOpen(false)}
                className="rounded-xl cursor-pointer"
              >
                Close
              </Button>
              <Button type="submit" disabled={resumeSubmitting} className="rounded-xl cursor-pointer font-medium">
                {resumeSubmitting ? 'Saving & Vectorizing…' : resume ? 'Update Resume' : 'Save Resume'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
