import { useNavigate } from 'react-router-dom'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Bookmark,
  Send,
  CalendarCheck,
  Award,
  XCircle,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Clock,
  Calendar,
  Building2,
} from 'lucide-react'

const statusConfig = {
  saved: {
    label: 'Saved',
    icon: Bookmark,
    iconColor: 'text-slate-500',
  },
  applied: {
    label: 'Applied',
    icon: Send,
    iconColor: 'text-blue-500',
  },
  interview: {
    label: 'Interview',
    icon: CalendarCheck,
    iconColor: 'text-amber-500',
  },
  offer: {
    label: 'Offer',
    icon: Award,
    iconColor: 'text-emerald-500',
  },
  rejected: {
    label: 'Rejected',
    icon: XCircle,
    iconColor: 'text-rose-500',
  },
}

const pipelineConfig = {
  completed: {
    label: 'Completed',
    icon: CheckCircle2,
    iconColor: 'text-emerald-500',
  },
  failed: {
    label: 'Failed',
    icon: AlertCircle,
    iconColor: 'text-rose-500',
  },
  running: {
    label: 'Analyzing…',
    icon: Loader2,
    iconColor: 'text-amber-500 animate-spin',
  },
  pending: {
    label: 'Pending',
    icon: Clock,
    iconColor: 'text-slate-400',
  },
}

export default function ApplicationCard({ application }) {
  const navigate = useNavigate()
  const { id, company, role, status, pipeline_status, created_at } = application

  const statusInfo = statusConfig[status] || {
    label: status,
    icon: Bookmark,
    iconColor: 'text-slate-500',
  }
  const StatusIcon = statusInfo.icon

  const pipelineInfo = pipelineConfig[pipeline_status] || pipelineConfig.pending
  const PipelineIcon = pipelineInfo.icon

  const formattedDate = created_at
    ? new Date(created_at).toLocaleDateString()
    : ''

  return (
    <Card
      className="cursor-pointer border-border bg-card hover:shadow-md hover:border-border/80 transition-all rounded-xl"
      onClick={() => navigate(`/applications/${id}`)}
    >
      <CardContent className="p-4 flex flex-col justify-between h-full gap-3.5">
        {/* Header row: Company logo/name & Role + Status Badge */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-2.5">
            <div className="h-9 w-9 rounded-lg border border-border bg-muted/40 flex items-center justify-center shrink-0 mt-0.5">
              <Building2 className="h-4 w-4 text-slate-600 dark:text-slate-400" />
            </div>
            <div>
              <p className="font-semibold text-card-foreground leading-tight">{company}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{role}</p>
            </div>
          </div>

          <Badge
            variant="outline"
            className="text-xs font-medium gap-1.5 py-1 px-2.5 rounded-lg border-border bg-background shrink-0"
          >
            <StatusIcon className={`h-3.5 w-3.5 ${statusInfo.iconColor}`} />
            <span>{statusInfo.label}</span>
          </Badge>
        </div>

        {/* Footer row: Pipeline status indicator & Date */}
        <div className="flex items-center justify-between pt-2.5 border-t border-border/60 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <PipelineIcon className={`h-3.5 w-3.5 ${pipelineInfo.iconColor}`} />
            <span>{pipelineInfo.label}</span>
          </div>

          {formattedDate && (
            <div className="flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5 text-slate-400" />
              <span>{formattedDate}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
