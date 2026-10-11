import { Progress } from '@/components/ui/progress'
import { Clock, Loader, CheckCircle, XCircle } from 'lucide-react'

const AGENTS = [
  { key: 'jd_parser', label: 'JD Parser' },
  { key: 'company_research', label: 'Company Research' },
  { key: 'interview_prep', label: 'Interview Prep' },
  { key: 'resume_tailor', label: 'Resume Tailor' },
  { key: 'cover_letter', label: 'Cover Letter' },
  { key: 'guardrails', label: 'Guardrails' },
  { key: 'synthesizer', label: 'Synthesizer' },
]

function getAgentStatus(key, messages) {
  const relevant = messages.filter((m) => m.agent === key)
  if (!relevant.length) return 'pending'
  const last = relevant[relevant.length - 1]
  return last.status || 'pending'
}

const icons = {
  pending: <Clock className="h-4 w-4 text-muted-foreground" />,
  running: <Loader className="h-4 w-4 animate-spin text-blue-500" />,
  completed: <CheckCircle className="h-4 w-4 text-green-500" />,
  failed: <XCircle className="h-4 w-4 text-red-500" />,
}

export default function AgentProgress({ messages = [] }) {
  const statuses = AGENTS.map((a) => getAgentStatus(a.key, messages))
  const completed = statuses.filter((s) => s === 'completed').length
  const progress = Math.round((completed / AGENTS.length) * 100)

  return (
    <div className="space-y-4">
      <Progress value={progress} />
      <div className="space-y-2">
        {AGENTS.map((agent, i) => {
          const status = statuses[i]
          return (
            <div key={agent.key} className="flex items-center gap-3 text-sm">
              {icons[status] || icons.pending}
              <span className={status === 'completed' ? 'text-muted-foreground line-through' : ''}>
                {agent.label}
              </span>
              <span className="ml-auto text-xs text-muted-foreground capitalize">{status}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
