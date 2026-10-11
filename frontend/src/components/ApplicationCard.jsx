import { useNavigate } from 'react-router-dom'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const statusStyles = {
  saved: 'secondary',
  applied: 'default',
  interview: 'default',
  offer: 'default',
  rejected: 'destructive',
}

const statusColors = {
  applied: 'bg-blue-500',
  interview: 'bg-yellow-500',
  offer: 'bg-green-500',
}

const pipelineDot = {
  completed: 'bg-green-500',
  running: 'bg-orange-400',
  failed: 'bg-red-500',
  pending: 'bg-gray-400',
}

export default function ApplicationCard({ application }) {
  const navigate = useNavigate()
  const { id, company, role, status, pipeline_status, created_at } = application

  const badgeVariant = statusStyles[status] || 'secondary'
  const badgeColor = statusColors[status]

  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={() => navigate(`/applications/${id}`)}
    >
      <CardContent className="p-4 flex flex-col gap-2">
        <div className="flex items-start justify-between">
          <div>
            <p className="font-semibold">{company}</p>
            <p className="text-sm text-muted-foreground">{role}</p>
          </div>
          <Badge
            variant={badgeVariant}
            className={badgeColor ? `${badgeColor} text-white border-transparent` : ''}
          >
            {status}
          </Badge>
        </div>
        <div className="flex items-center justify-between mt-1">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className={`h-2 w-2 rounded-full ${pipelineDot[pipeline_status] || 'bg-gray-400'}`} />
            {pipeline_status}
          </div>
          <span className="text-xs text-muted-foreground">
            {new Date(created_at).toLocaleDateString()}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}
