'use client'
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { 
  Zap, 
  Terminal, 
  ChevronRight, 
  CheckCircle2, 
  Timer, 
  Activity,
  ArrowRight,
  Sparkles
} from 'lucide-react'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { cn } from "@/lib/utils"

export default function ProcessingPage() {
  const { id } = useParams()
  const router = useRouter()
  const searchParams = useSearchParams()
  const [taskStatus, setTaskStatus] = useState<any>(null)
  const [logs, setLogs] = useState<string[]>([])
  const [isCompleted, setIsCompleted] = useState(false)

  useEffect(() => {
    if (!id) return;

    const eventSource = new EventSource(`http://localhost:8000/tasks/${id}/progress?user_id=local_user`);

    eventSource.onmessage = (event) => {
       const data = JSON.parse(event.data);
       setTaskStatus(data);
       
       if (data.status === "completed") {
          setIsCompleted(true)
          eventSource.close();
       }
       
       const newLog = getLogForStatus(data.status?.toUpperCase(), data.progress);
       if (newLog && !logs.includes(newLog)) {
          setLogs(prev => [...prev.slice(-15), newLog]);
       }
    };

    eventSource.onerror = (err) => {
       console.error("SSE Error:", err);
       eventSource.close();
    };

    return () => eventSource.close();
  }, [id]);

  const getLogForStatus = (status: string, progress: number) => {
    if (status === "QUEUED") return `[SYSTEM] Task ${id?.slice(0, 8)} queued in Redis...`
    if (status === "DOWNLOADING") return `[DOWNLOAD] Extracting media stream... ${progress}%`
    if (status === "TRANSCRIBING") return `[AI] Speech-to-Text: Processing language patterns...`
    if (status === "ANALYZING") return `[LLM] Llama 3: Scanning for viral hooks and retention spikes...`
    if (status === "CLIPPING") return `[SYSTEM] FFmpeg: Trimming segments and applying dynamic zoom...`
    if (status === "COMPLETED") return `✅ AI Analysis complete! Generated viral clips successfully.`
    return null;
  }

  return (
    <div className="min-h-full flex flex-col items-center justify-center p-8 max-w-4xl mx-auto">
      
      {/* Processing Animation */}
      <div className="relative mb-12">
        <div className="w-48 h-48 rounded-full border-4 border-white/5 flex items-center justify-center relative overflow-hidden">
           {/* Pulsing Glow */}
           <motion.div 
             animate={{ scale: [1, 1.2, 1], opacity: [0.1, 0.3, 0.1] }}
             transition={{ duration: 4, repeat: Infinity }}
             className="absolute inset-4 bg-blue-500 rounded-full blur-3xl"
           />

           <div className="relative z-10 text-center">
              <span className="text-5xl font-black text-white">{taskStatus?.progress || 0}%</span>
              <p className="text-[10px] font-bold text-blue-400 uppercase tracking-widest mt-1">Progress</p>
           </div>
           
           {/* SVG Ring Progress */}
           <svg className="absolute inset-0 -rotate-90 w-full h-full">
              <circle
                cx="96" cy="96" r="92"
                stroke="currentColor"
                strokeWidth="4"
                fill="transparent"
                className="text-blue-500 transition-all duration-700"
                style={{
                   strokeDasharray: '580',
                   strokeDashoffset: 580 - (580 * (taskStatus?.progress || 0)) / 100
                }}
              />
           </svg>
        </div>
      </div>

      <div className="text-center mb-8">
        <h2 className="text-4xl font-black mb-2 tracking-tight">AI đang "đúc" nội dung của bạn</h2>
        <p className="text-zinc-500 font-medium">Vui lòng không đóng trang này để quá trình diễn ra liên tục.</p>
      </div>

      {/* Main Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full mb-8">
         <StatusStep 
            icon={Timer} 
            label="Phân tích" 
            isActive={taskStatus?.status === 'ANALYZING' || taskStatus?.status === 'TRANSCRIBING'}
            isDone={['CLIPPING', 'COMPLETED'].includes(taskStatus?.status?.toUpperCase())}
         />
         <StatusStep 
            icon={Activity} 
            label="Cắt ghép" 
            isActive={taskStatus?.status === 'CLIPPING'} 
            isDone={taskStatus?.status === 'COMPLETED'}
         />
         <StatusStep 
            icon={Sparkles} 
            label="Sẵn sàng" 
            isActive={false}
            isDone={taskStatus?.status === 'COMPLETED'}
         />
      </div>

      {/* Terminal Log View */}
      <div className="w-full bg-black/40 border border-white/5 rounded-3xl p-6 font-mono text-xs overflow-hidden relative group">
         <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-4">
            <div className="flex items-center gap-2">
               <Terminal className="w-4 h-4 text-zinc-500" />
               <span className="text-[10px] text-zinc-500 uppercase tracking-widest font-bold">Process Engine Log</span>
            </div>
            <div className="flex gap-1.5">
               <div className="w-2 h-2 rounded-full bg-red-500/20" />
               <div className="w-2 h-2 rounded-full bg-amber-500/20" />
               <div className="w-2 h-2 rounded-full bg-green-500/20" />
            </div>
         </div>

         <div className="space-y-3 h-48 overflow-y-auto custom-scrollbar pr-2">
            <AnimatePresence>
               {logs.map((log, i) => (
                  <motion.p 
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className={cn(
                       "flex items-start gap-2",
                       log.startsWith('✅') ? "text-green-500 bg-green-500/5 p-2 rounded-lg" : "text-zinc-500"
                    )}
                  >
                     <ChevronRight className="w-3 h-3 mt-0.5 shrink-0" />
                     {log}
                  </motion.p>
               ))}
            </AnimatePresence>
            {!isCompleted && (
              <div className="flex items-center gap-2 text-blue-400 animate-pulse">
                <div className="w-1.5 h-1.5 bg-blue-500 rounded-full" />
                <span>Running analysis engine...</span>
              </div>
            )}
         </div>
      </div>

      <AnimatePresence>
         {isCompleted && (
            <motion.div 
               initial={{ opacity: 0, y: 20 }}
               animate={{ opacity: 1, y: 0 }}
               className="mt-12 flex items-center justify-center"
            >
               <Button 
                  onClick={() => router.push(`/gallery`)}
                  size="lg"
                  className="bg-blue-500 hover:bg-blue-600 text-white font-bold h-14 px-10 rounded-2xl shadow-xl shadow-blue-500/20"
               >
                  Xem kết quả Viral ngay <ArrowRight className="ml-2 w-5 h-5 underline decoration-blue-300" />
               </Button>
            </motion.div>
         )}
      </AnimatePresence>
    </div>
  )
}

function StatusStep({ icon: Icon, label, isActive, isDone }: any) {
  return (
    <div className={cn(
      "p-6 rounded-3xl border transition-all duration-500 flex flex-col items-center gap-2",
      isActive ? "bg-blue-500/10 border-blue-500/30 ring-4 ring-blue-500/5 scale-105" : "bg-white/5 border-white/5 scale-100",
      isDone && "bg-green-500/10 border-green-500/30 opacity-60"
    )}>
      <div className={cn(
         "w-12 h-12 rounded-2xl flex items-center justify-center transition-colors",
         isActive ? "bg-blue-500 text-white" : isDone ? "bg-green-500 text-white" : "bg-zinc-800 text-zinc-500"
      )}>
         {isDone ? <CheckCircle2 className="w-6 h-6" /> : <Icon className={cn("w-6 h-6", isActive && "animate-spin")} />}
      </div>
      <span className={cn(
         "text-[10px] font-black uppercase tracking-widest",
         isActive ? "text-blue-500" : isDone ? "text-green-500" : "text-zinc-600"
      )}>{label}</span>
      {isActive && (
         <div className="text-[9px] text-blue-400/60 font-bold bg-blue-400/10 px-2 py-0.5 rounded-full mt-1">Active</div>
      )}
    </div>
  )
}
