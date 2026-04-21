'use client'
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MoreVertical, Play, Clock, Share2, Trash2, Loader2, AlertCircle } from 'lucide-react'
import Image from 'next/image'
import { Button } from '@/components/ui/button'
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu'
import { useRouter } from 'next/navigation'

interface Task {
  id: string
  source_title: string
  status: string
  clips_count: number
  created_at: string
}

export function RecentProjects() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const res = await fetch("http://localhost:8000/tasks/", {
           headers: { "user_id": "local_user" }
        })
        if (!res.ok) throw new Error("Failed to fetch tasks")
        const data = await res.json()
        setTasks(data.tasks || [])
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchTasks()
  }, [])

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      const now = new Date()
      const diffInHrs = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))
      
      if (diffInHrs < 1) return 'Vừa xong'
      if (diffInHrs < 24) return `${diffInHrs} giờ trước`
      return date.toLocaleDateString('vi-VN')
    } catch (e) {
      return dateString
    }
  }

  // Generate a consistent placeholder image based on task ID
  const getThumbnail = (id: string) => {
    const seeds = ['curry', 'nature', 'tech', 'city', 'portrait', 'vlog']
    const seed = seeds[id.charCodeAt(0) % seeds.length]
    return `https://images.unsplash.com/photo-${id.length > 10 ? '1546069901-ba9599a7e63c' : '1517694712202-14dd9538aa97'}?w=400&h=400&q=80&sig=${id.slice(0,5)}`
  }

  if (loading) {
     return (
        <div className="py-20 flex flex-col items-center justify-center text-zinc-500 gap-4">
           <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
           <p className="text-sm font-bold uppercase tracking-widest">Đang tải dự án thực tế...</p>
        </div>
     )
  }

  if (error) {
     return (
        <div className="py-20 border-2 border-dashed border-red-500/20 rounded-[40px] flex flex-col items-center justify-center text-red-400 gap-2">
           <AlertCircle className="w-8 h-8" />
           <p className="text-lg font-bold">Lỗi khi tải dự án</p>
           <p className="text-sm">{error}</p>
        </div>
     )
  }

  if (tasks.length === 0) {
     return (
        <div className="py-20 border-2 border-dashed border-white/5 rounded-[40px] flex flex-col items-center justify-center text-zinc-600 gap-2">
           <p className="text-lg font-bold">Chưa có dự án nào</p>
           <p className="text-sm">Hãy bắt đầu bằng cách dán một link video ở trên!</p>
        </div>
     )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {tasks.map((task, idx) => (
        <motion.div
           key={task.id}
           initial={{ opacity: 0, scale: 0.9 }}
           animate={{ opacity: 1, scale: 1 }}
           transition={{ delay: idx * 0.05 }}
           className="group relative bg-zinc-900 border border-white/5 rounded-3xl overflow-hidden hover:border-blue-500/50 transition-all duration-300 shadow-xl"
        >
          {/* Thumbnail area */}
          <div className="relative aspect-video overflow-hidden cursor-pointer" onClick={() => router.push(task.status === 'completed' ? `/gallery?task_id=${task.id}` : `/processing/${task.id}`)}>
            <Image 
              src={getThumbnail(task.id)} 
              alt={task.source_title || 'Untitled Project'} 
              fill
              className="object-cover group-hover:scale-110 transition-transform duration-700 opacity-60 group-hover:opacity-100"
            />
            {/* Status Overlay */}
            <div className="absolute inset-0 bg-black/20 group-hover:bg-transparent transition-colors" />
            
            <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
               <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-2xl scale-75 group-hover:scale-100 transition-transform duration-300">
                  <Play className="w-6 h-6 text-black fill-current ml-1" />
               </div>
            </div>

            {/* Top Right Actions */}
            <div className="absolute top-3 right-3 z-30">
               <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button className="w-8 h-8 rounded-full bg-black/60 backdrop-blur-md flex items-center justify-center text-white/70 hover:text-white border border-white/10 transition-colors outline-none translate-x-4 opacity-0 group-hover:translate-x-0 group-hover:opacity-100 transition-all">
                       <MoreVertical className="w-4 h-4" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-48 bg-zinc-950 border-white/10 rounded-2xl p-2 shadow-2xl">
                     <DropdownMenuItem className="flex items-center gap-2 p-2.5 cursor-pointer rounded-xl hover:bg-white/5 focus:bg-white/5 transition-colors">
                        <Share2 className="w-4 h-4 text-blue-400" />
                        <span className="text-sm font-medium">Share Project</span>
                     </DropdownMenuItem>
                     <DropdownMenuItem className="flex items-center gap-2 p-2.5 cursor-pointer rounded-xl hover:bg-red-500/10 focus:bg-red-500/10 text-red-500 transition-colors">
                        <Trash2 className="w-4 h-4" />
                        <span className="text-sm font-medium">Delete Forever</span>
                     </DropdownMenuItem>
                  </DropdownMenuContent>
               </DropdownMenu>
            </div>

            {/* Badge for status */}
            <div className="absolute top-3 left-3 px-2 py-1 bg-black/60 backdrop-blur-md rounded-lg text-[9px] font-black uppercase tracking-widest text-white border border-white/10">
               {task.status === 'completed' ? 'Success' : task.status === 'processing' ? 'Processing' : 'Queued'}
            </div>
          </div>

          {/* Details */}
          <div className="p-5">
            <h4 className="font-bold text-sm text-white/90 truncate mb-1 group-hover:text-blue-400 transition-all">
               {task.source_title || `Project #${task.id.slice(0,4)}`}
            </h4>
            <div className="flex items-center justify-between">
               <div className="flex items-center gap-1.5 text-[10px] text-zinc-500 font-bold">
                  <Clock className="w-3 h-3" />
                  <span>{formatDate(task.created_at)}</span>
               </div>
               <div className="flex items-center gap-1.5">
                  <div className="px-2 py-0.5 bg-blue-500/10 border border-blue-500/20 text-blue-400 rounded-lg font-black text-[9px] uppercase">
                     {task.clips_count} clips
                  </div>
               </div>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  )
}
