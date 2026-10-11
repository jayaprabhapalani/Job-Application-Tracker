import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '@/api/client'
import Navbar from '@/components/Navbar'
import ApplicationCard from '@/components/ApplicationCard'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'

const STATUSES = ['saved', 'applied', 'interview', 'offer', 'rejected']

function StatCard({ label, count }) {
  return (
    <Card className="flex-1">
      <CardContent className="p-4">
        <p className="text-2xl font-bold">{count}</p>
        <p className="text-sm text-muted-foreground">{label}</p>
      </CardContent>
    </Card>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [applications, setApplications] = useState([])
  const [loadingApps, setLoadingApps] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    client.get('/jobs/').then(({ data }) => setApplications(data)).finally(() => setLoadingApps(false))
  }, [])

  const counts = {
    Total: applications.length,
    Applied: applications.filter((a) => a.status === 'applied').length,
    Interviews: applications.filter((a) => a.status === 'interview').length,
    Offers: applications.filter((a) => a.status === 'offer').length,
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    const form = new FormData(e.target)
    try {
      const { data } = await client.post('/jobs/', {
        company: form.get('company'),
        role: form.get('role'),
        jd_text: form.get('jd_text') || ' ',
        jd_url: form.get('jd_url') || undefined,
      })
      navigate(`/applications/${data.id}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create application')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">

        {/* Stats */}
        <div className="flex gap-4">
          {Object.entries(counts).map(([label, count]) => (
            <StatCard key={label} label={label} count={count} />
          ))}
        </div>

        {/* New Application */}
        <Card>
          <CardHeader>
            <CardTitle>New Application</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <Label htmlFor="company">Company name</Label>
                  <Input id="company" name="company" required />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="role">Role</Label>
                  <Input id="role" name="role" required />
                </div>
              </div>
              <div className="space-y-1">
                <Label htmlFor="jd_text">Job description</Label>
                <Textarea
                  id="jd_text"
                  name="jd_text"
                  rows={6}
                  placeholder="Paste job description here"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="jd_url">Or paste a URL instead</Label>
                <Input id="jd_url" name="jd_url" type="url" placeholder="https://..." />
              </div>
              <Button type="submit" disabled={submitting}>
                {submitting ? 'Submitting…' : 'Submit'}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Applications list */}
        <div>
          <h2 className="font-semibold text-lg mb-4">Applications</h2>
          {loadingApps ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-28 rounded-xl" />
              ))}
            </div>
          ) : applications.length === 0 ? (
            <p className="text-muted-foreground text-sm">No applications yet. Add your first one above.</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {applications.map((app) => (
                <ApplicationCard key={app.id} application={app} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
