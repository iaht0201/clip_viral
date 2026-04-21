'use client'
import { Bell, Search, User, CreditCard, LogOut, Settings as SettingsIcon } from 'lucide-react'
import Image from 'next/image'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import { usePathname } from 'next/navigation'

export function Topbar() {
  const pathname = usePathname()
  
  const getPageTitle = (path: string) => {
    if (path === '/') return 'AI Studio'
    if (path === '/gallery') return 'Clip Gallery'
    if (path === '/editor') return 'Pro Editor'
    if (path === '/settings') return 'Settings'
    if (path.includes('/processing')) return 'Processing Video'
    if (path.includes('/quick-edit')) return 'Quick Edit'
    return 'Dashboard'
  }

  return (
    <header className="h-20 border-b border-white/5 bg-zinc-950/30 backdrop-blur-md flex items-center justify-between px-8 z-50">
      <div className="flex items-center gap-8">
        <h2 className="text-xl font-bold tracking-tight text-white/90">
          {getPageTitle(pathname)}
        </h2>

        <div className="hidden md:flex relative items-center group">
          <Search className="w-4 h-4 absolute left-4 text-zinc-500 group-focus-within:text-blue-400 transition-colors" />
          <input 
            type="text" 
            placeholder="Search projects or clips..." 
            className="bg-white/5 border border-white/5 rounded-2xl py-2.5 pl-11 pr-6 text-sm w-80 outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500/50 transition-all placeholder:text-zinc-600"
          />
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 px-4 py-1.5 bg-gradient-to-br from-amber-500/10 to-amber-600/10 border border-amber-500/20 rounded-full text-amber-500">
           <Zap className="w-3.5 h-3.5 fill-current" />
           <span className="text-[10px] font-black uppercase tracking-widest">Self Hosted</span>
        </div>

        <button className="relative w-10 h-10 flex items-center justify-center text-zinc-500 hover:text-white transition-colors">
          <Bell className="w-5 h-5" />
          <div className="absolute top-2.5 right-2.5 w-2 h-2 bg-blue-500 rounded-full shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
        </button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-3 p-1.5 hover:bg-white/5 rounded-2xl transition-all border border-transparent hover:border-white/5">
              <div className="w-10 h-10 rounded-xl overflow-hidden border border-white/10 p-0.5 bg-gradient-to-br from-blue-500/20 to-purple-500/20">
                <Image 
                  src="https://api.dicebear.com/7.x/avataaars/svg?seed=LocalUser" 
                  alt="Avatar" 
                  width={40} 
                  height={40}
                  className="rounded-lg"
                />
              </div>
              <div className="hidden lg:block text-left pr-2">
                <p className="text-xs font-bold text-white/90">Local Dev</p>
                <p className="text-[10px] text-zinc-500 font-mono">thaidq@gmail.com</p>
              </div>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56 bg-zinc-900 border-white/5 rounded-2xl p-2 shadow-2xl">
            <DropdownMenuLabel className="text-xs text-zinc-500 uppercase tracking-widest px-3 py-2">Account</DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-white/5" />
            <DropdownMenuItem className="flex items-center gap-3 p-3 cursor-pointer rounded-xl hover:bg-white/5 focus:bg-white/5 transition-colors">
              <User className="w-4 h-4 text-blue-400" />
              <span className="text-sm">Profile Settings</span>
            </DropdownMenuItem>
            <DropdownMenuItem className="flex items-center gap-3 p-3 cursor-pointer rounded-xl hover:bg-white/5 focus:bg-white/5 transition-colors">
              <CreditCard className="w-4 h-4 text-purple-400" />
              <span className="text-sm">Local Plan</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator className="bg-white/5" />
            <DropdownMenuItem className="flex items-center gap-3 p-3 cursor-pointer rounded-xl hover:bg-white/10 text-red-400 focus:bg-red-500/10 focus:text-red-400 transition-colors">
              <LogOut className="w-4 h-4" />
              <span className="text-sm font-bold">Sign Out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}

function Zap({ className }: { className?: string }) {
  return (
    <svg 
      className={className} 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round"
    >
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  )
}
