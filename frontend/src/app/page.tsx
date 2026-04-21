'use client'
import { motion } from 'framer-motion'
import { Sparkles, History, Video, ArrowRight } from 'lucide-react'
import { Dropzone } from '@/components/ai-studio/Dropzone'
import { RecentProjects } from '@/components/ai-studio/RecentProjects'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

export default function AIStudioHome() {
  const router = useRouter()
  const [isCreatingTask, setIsCreatingTask] = useState(false)

  const handleStartAnalysis = async (url: string) => {
    setIsCreatingTask(true)
    try {
      const res = await fetch("http://localhost:8000/tasks/create/clips", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "user_id": "local_user" 
        },
        body: JSON.stringify({ source: { url } })
      })
      const data = await res.json()
      if (data.task_id) {
         router.push(`/processing/${data.task_id}`)
      }
    } catch (err) {
      console.error("Task creation failed:", err)
    } finally {
      setIsCreatingTask(false)
    }
  }

  return (
    <div className="min-h-full py-16 px-4 md:px-8 max-w-7xl mx-auto">
      {/* Hero Section */}
      <div className="text-center mb-20 relative">
        <motion.div
           initial={{ opacity: 0, scale: 0.8 }}
           animate={{ opacity: 1, scale: 1 }}
           className="inline-flex items-center gap-2 px-3 py-1 bg-blue-500/10 border border-blue-500/20 text-blue-400 rounded-full text-xs font-bold uppercase tracking-widest mb-6"
        >
           <Sparkles className="w-3 h-3 fill-current" /> Next-Gen AI Clipping
        </motion.div>
        
        <motion.h1 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-6xl md:text-7xl font-black bg-gradient-to-r from-white via-white to-white/40 bg-clip-text text-transparent mb-6 tracking-tight"
        >
          ReelShort AI <span className="text-blue-500">Studio</span>
        </motion.h1>
        
        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="text-xl text-zinc-400 max-w-2xl mx-auto font-medium"
        >
          Nền tảng trí tuệ nhân tạo thế hệ mới: Biến video dài thành hàng loạt Clip Viral chỉ trong 3 phút.
        </motion.p>

        {/* Global Glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-blue-500/5 blur-[120px] rounded-full pointer-events-none" />
      </div>

      <Dropzone onAnalyze={handleStartAnalysis} />

      {/* Stats/Social Proof (Quick Row) */}
      <div className="mt-16 flex flex-wrap justify-center gap-12 border-y border-white/5 py-10 opacity-60 grayscale hover:grayscale-0 transition-all">
         <div className="flex flex-col items-center">
            <span className="text-2xl font-black text-white">100%</span>
            <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Accuracy</span>
         </div>
         <div className="flex flex-col items-center border-l border-white/10 pl-12">
            <span className="text-2xl font-black text-white">4K</span>
            <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Quality</span>
         </div>
         <div className="flex flex-col items-center border-l border-white/10 pl-12">
            <span className="text-2xl font-black text-white">0.5s</span>
            <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Latency</span>
         </div>
         <div className="flex flex-col items-center border-l border-white/10 pl-12">
            <span className="text-2xl font-black text-white">SOTA</span>
            <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">LLM Backend</span>
         </div>
      </div>

      {/* Recent Projects Section */}
      <div className="mt-28 mb-20">
        <div className="flex items-center justify-between mb-10">
          <div className="flex items-center gap-4">
             <div className="w-12 h-12 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center text-blue-400">
                <History className="w-6 h-6" />
             </div>
             <div>
                <h2 className="text-3xl font-black tracking-tight text-white/90">Dự án gần đây</h2>
                <p className="text-sm text-zinc-500 font-medium">Lịch sử các video AI đã phân tích của bạn</p>
             </div>
          </div>
          <button className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors text-sm font-bold group">
             Xem tất cả dự án <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
        
        <RecentProjects />
      </div>

      {/* Loading Overlay for redirection */}
      {isCreatingTask && (
         <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-xl flex flex-col items-center justify-center"
         >
            <div className="w-16 h-16 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin mb-6" />
            <h3 className="text-2xl font-bold mb-2">Đang khởi tạo Task AI...</h3>
            <p className="text-zinc-500 animate-pulse">Vui lòng chờ trong giây lát</p>
         </motion.div>
      )}
    </div>
  )
}
