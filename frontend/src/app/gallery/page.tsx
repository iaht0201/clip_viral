'use client'
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useSearchParams, useRouter } from 'next/navigation'
import { 
  Sparkles, 
  Filter, 
  LayoutGrid, 
  ArrowLeft, 
  Share2, 
  Download,
  AlertCircle,
  Clock,
  CheckCircle2
} from 'lucide-react'
import { ClipCard } from '@/components/gallery/ClipCard'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'

export default function GalleryPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const taskId = searchParams.get('task_id') || searchParams.get('id')
  const [clips, setClips] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchClips = async () => {
      if (!taskId) {
        setLoading(false)
        return
      }

      try {
        const res = await fetch(`http://localhost:8000/tasks/${taskId}/clips`, {
           headers: { "user_id": "local_user" }
        })
        if (!res.ok) throw new Error("Could not fetch clips for this task")
        const data = await res.json()
        setClips(data.clips || [])
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchClips()
  }, [taskId])

  return (
    <div className="min-h-full p-8 lg:p-12 max-w-[1600px] mx-auto">
      
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
        <div className="space-y-4">
           <button 
             onClick={() => router.push('/')}
             className="flex items-center gap-2 text-zinc-500 hover:text-white transition-colors text-xs font-bold uppercase tracking-widest group"
           >
              <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" /> Quay lại AI Studio
           </button>
           
           <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-blue-500 rounded-3xl flex items-center justify-center shadow-2xl shadow-blue-500/20">
                 <Sparkles className="w-8 h-8 text-white fill-current" />
              </div>
              <div>
                 <h1 className="text-4xl lg:text-5xl font-black bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent tracking-tight">
                    Kết quả <span className="text-blue-500">Viral</span>
                 </h1>
                 <p className="text-zinc-500 font-medium">Tìm thấy {clips.length} khoảnh khắc đắt giá cho video của bạn</p>
              </div>
           </div>
        </div>

        <div className="flex items-center gap-3">
           <Button variant="outline" className="h-14 px-8 rounded-2xl bg-white/5 border-white/5 hover:bg-white/10 text-white font-bold text-sm">
              <Download className="mr-2 w-4 h-4 text-blue-400" /> Tải về tất cả (.zip)
           </Button>
           <Button className="h-14 px-8 rounded-2xl bg-blue-500 hover:bg-blue-600 text-white font-bold text-sm shadow-xl shadow-blue-500/20">
              <Share2 className="mr-2 w-4 h-4" /> Chia sẻ dự án
           </Button>
        </div>
      </div>

      <div className="w-full h-px bg-white/5 mb-12" />

      {/* Error State */}
      {error && (
         <div className="p-20 flex flex-col items-center justify-center text-center">
            <div className="w-20 h-20 bg-red-500/10 rounded-full flex items-center justify-center mb-6">
               <AlertCircle className="w-10 h-10 text-red-500" />
            </div>
            <h3 className="text-2xl font-bold mb-2">Đã xảy ra lỗi</h3>
            <p className="text-zinc-500 max-w-sm mx-auto mb-8">{error}</p>
            <Button onClick={() => window.location.reload()} variant="link" className="text-blue-500">Thử lại</Button>
         </div>
      )}

      {/* Empty State */}
      {!loading && !error && clips.length === 0 && (
         <div className="p-24 flex flex-col items-center justify-center text-center bg-zinc-900/30 border border-dashed border-white/5 rounded-[48px]">
            <div className="w-24 h-24 bg-white/5 rounded-full flex items-center justify-center mb-8 relative">
               <LayoutGrid className="w-10 h-10 text-zinc-700" />
               <div className="absolute top-0 right-0 w-6 h-6 bg-amber-500 rounded-full flex items-center justify-center text-black border-4 border-zinc-950">
                  <Clock className="w-3 h-3 font-bold" />
               </div>
            </div>
            <h3 className="text-3xl font-black mb-4 tracking-tight">Chưa có clip nào sẵn sàng</h3>
            <p className="text-zinc-500 max-w-md mx-auto mb-10 text-lg">AI của chúng tôi cần thêm chút thời gian để hoàn thành việc bóc tách và phân tích điểm số Viral cho video này.</p>
            <Button onClick={() => router.push('/')} variant="outline" className="h-12 px-10 rounded-xl border-white/10 hover:bg-white/5 text-white">
               Về trang chủ
            </Button>
         </div>
      )}

      {/* Clips Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 xxl:grid-cols-5 gap-8">
         <AnimatePresence>
            {loading ? (
               Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="aspect-[9/16] rounded-[48px] bg-white/5 animate-pulse border border-white/5" />
               ))
            ) : (
               clips.map((clip, idx) => (
                  <motion.div
                    key={clip.id}
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.05, type: 'spring', damping: 20 }}
                  >
                     <ClipCard clip={clip} />
                  </motion.div>
               ))
            )}
         </AnimatePresence>
      </div>

      {/* Task Final Info */}
      {!loading && clips.length > 0 && (
         <div className="mt-24 p-8 bg-gradient-to-r from-blue-500/5 to-purple-600/5 border border-white/5 rounded-[40px] flex flex-col md:flex-row items-center justify-between gap-8">
            <div className="flex items-center gap-6">
               <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center border border-green-500/10">
                  <CheckCircle2 className="w-8 h-8 text-green-500" />
               </div>
               <div>
                  <h4 className="text-2xl font-black text-white/90 mb-1 leading-tight">Phân tích hoàn tất</h4>
                  <p className="text-zinc-500 font-medium">Project ID: <span className="font-mono text-xs">{taskId}</span></p>
               </div>
            </div>
            
            <div className="flex items-center gap-4">
               <div className="text-right hidden sm:block">
                  <p className="text-xs font-bold text-zinc-500 uppercase tracking-widest">Thời gian xử lý</p>
                  <p className="text-sm font-medium text-white/80">3 phút 12 giây</p>
               </div>
               <div className="w-px h-10 bg-white/10 mx-4 hidden sm:block" />
               <Button className="h-14 px-8 rounded-2xl bg-white text-black font-black hover:bg-zinc-200 transition-all shadow-xl shadow-white/5">
                  TIẾP TỤC VỚI VIDEO KHÁC
               </Button>
            </div>
         </div>
      )}
    </div>
  )
}
