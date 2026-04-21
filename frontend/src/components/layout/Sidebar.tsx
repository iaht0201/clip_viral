'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { 
  Home, 
  Video, 
  Layers, 
  Settings, 
  Zap, 
  Clock, 
  HelpCircle,
  Scissors
} from 'lucide-react'
import { cn } from '@/lib/utils'

const sidebarItems = [
  { name: 'AI Studio', icon: Zap, href: '/' },
  { name: 'My Gallery', icon: Video, href: '/gallery' },
  { name: 'Pro Editor', icon: Scissors, href: '/editor' },
  { name: 'Projects', icon: Layers, href: '/projects' },
  { name: 'History', icon: Clock, href: '/history' },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-64 border-r border-white/5 bg-zinc-950/50 backdrop-blur-xl flex flex-col">
      <div className="p-6">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Zap className="w-6 h-6 text-white fill-current" />
          </div>
          <span className="text-xl font-black bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
            ReelShort
          </span>
        </Link>
      </div>

      <nav className="flex-1 px-4 space-y-1.5 mt-4">
        {sidebarItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link key={item.name} href={item.href}>
              <div
                className={cn(
                  "group relative flex items-center gap-3 px-4 py-3 rounded-2xl transition-all duration-300",
                  isActive 
                    ? "bg-white/5 text-blue-400" 
                    : "text-zinc-500 hover:text-white hover:bg-white/[0.03]"
                )}
              >
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active"
                    className="absolute left-0 w-1 h-3/5 bg-blue-500 rounded-r-full"
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  />
                )}
                <item.icon className={cn("w-5 h-5", isActive ? "text-blue-400" : "group-hover:scale-110 transition-transform")} />
                <span className="text-sm font-medium">{item.name}</span>
              </div>
            </Link>
          )
        })}
      </nav>

      <div className="p-4 border-t border-white/5 flex flex-col gap-2">
         <Link href="/settings" className="flex items-center gap-3 px-4 py-3 text-zinc-500 hover:text-white hover:bg-white/[0.03] rounded-2xl transition-all">
            <Settings className="w-5 h-5" />
            <span className="text-sm font-medium">Settings</span>
         </Link>
         <div className="p-4 bg-gradient-to-br from-blue-500/5 to-purple-500/5 border border-white/5 rounded-2xl mt-2 overflow-hidden relative">
            <div className="relative z-10">
               <p className="text-[10px] font-bold text-blue-400 uppercase tracking-widest mb-1">Local Plan</p>
               <p className="text-xs text-zinc-400">Unlimited AI processing</p>
            </div>
            <div className="absolute top-0 right-0 w-16 h-16 bg-blue-500/5 blur-2xl rounded-full translate-x-1/2 -translate-y-1/2" />
         </div>
      </div>
    </aside>
  )
}
