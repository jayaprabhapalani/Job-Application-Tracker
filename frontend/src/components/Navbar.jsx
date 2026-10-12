import { Link } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Sparkles, LogOut, ChevronDown } from 'lucide-react'

export default function Navbar() {
  const { user, logout } = useAuth()
  const userInitials = user?.sub ? user.sub.slice(0, 2).toUpperCase() : 'JP'

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border/60 bg-background/95 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link to="/dashboard" className="flex items-center gap-2.5 group">
          <div className="h-9 w-9 rounded-xl border border-border bg-card flex items-center justify-center text-blue-600 shadow-xs group-hover:border-blue-500/40 transition-colors">
            <Sparkles className="h-4 w-4 text-blue-600" />
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-lg leading-tight tracking-tight text-foreground flex items-center gap-1.5">
              JobPilot
              <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded-md border border-border text-muted-foreground">
                AI
              </span>
            </span>
          </div>
        </Link>

        {/* User profile dropdown */}
        {user && (
          <div className="flex items-center gap-3">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="flex items-center gap-2 pl-2 pr-3 py-1.5 rounded-full hover:bg-muted/80 border border-border/50 transition-colors"
                >
                  <Avatar className="h-7 w-7 text-xs font-semibold bg-muted text-foreground">
                    <AvatarFallback>{userInitials}</AvatarFallback>
                  </Avatar>
                  <span className="text-sm font-medium text-foreground max-w-[140px] truncate hidden sm:inline-block">
                    {user.sub}
                  </span>
                  <ChevronDown className="h-3.5 w-3.5 text-muted-foreground opacity-70" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 mt-1 rounded-xl shadow-lg border-border/80 p-1.5">
                <DropdownMenuLabel className="font-normal px-2 py-1.5">
                  <div className="flex flex-col space-y-1">
                    <p className="text-xs text-muted-foreground">Signed in as</p>
                    <p className="text-sm font-medium text-foreground truncate">{user.sub}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator className="my-1" />
                <DropdownMenuItem
                  onClick={logout}
                  className="flex items-center gap-2 text-destructive focus:text-destructive focus:bg-destructive/10 cursor-pointer rounded-lg px-2 py-1.5"
                >
                  <LogOut className="h-4 w-4" />
                  <span>Sign out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
      </div>
    </header>
  )
}
