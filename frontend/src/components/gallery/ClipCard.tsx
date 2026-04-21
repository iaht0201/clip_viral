'use client'
import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Play, 
  Flame, 
  Timer, 
  Scissors, 
  Download, 
  ExternalLink,
  Target,
  Zap,
  Star
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import Link from 'next/link'

interface ClipCardProps {
  clip: {
    id: string
    video_url: string
    virality_score: number
    hook_score: number
    engagement_score: number
    duration: number
    title?: string
    reasoning?: string
  }
}

export function ClipCard({ clip }: ClipCardProps) {
  const [isHovered, setIsHovered] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)

  const handleMouseEnter = () => {
    setIsHovered(true)
    videoRef.current?.play().catch(e => console.log("Autoplay blocked"))
  }

  const handleMouseLeave = () => {
    setIsHovered(false)
    videoRef.current?.pause()
    if (videoRef.current) videoRef.current.currentTime = 0
  }

  const getViralityColor = (score: number) => {
    if (score >= 90) return 'from-orange-500 to-red-600 shadow-orange-500/50 text-white'
    if (score >= 80) return 'from-amber-400 to-orange-500 shadow-amber-500/50 text-white'
    return 'from-blue-400 to-blue-600 shadow-blue-500/50 text-white'
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className="group relative bg-zinc-900 border border-white/5 rounded-3xl overflow-hidden hover:border-blue-500/50 hover:shadow-2xl hover:shadow-blue-500/10 transition-all duration-500"
    >
      {/* Video Preview */}
      <div className="relative aspect-[9/16] bg-black overflow-hidden">
        <video
          ref={videoRef}
          src={clip.video_url.startsWith('http') ? clip.video_url : `http://localhost:8000${clip.video_url}`}
          className="absolute inset-0 w-full h-full object-cover opacity-60 group-hover:opacity-100 transition-opacity duration-700"
          muted
          loop
          playsInline
        />
        
        {/* Top Info Overlay */}
        <div className="absolute top-4 left-4 right-4 flex justify-between items-start z-20">
           <div className={cn(
             "px-3 py-1.5 rounded-full bg-gradient-to-r flex items-center gap-1.5 font-black text-xs shadow-lg",
             getViralityColor(clip.virality_score)
           )}>
              <Flame className="w-4 h-4 fill-current" />
              {clip.virality_score} 🔥
           </div>
           
           <div className="bg-black/60 backdrop-blur-md px-2 py-1 rounded-lg text-[10px] font-bold text-white border border-white/10 flex items-center gap-1.5">
              <Timer className="w-3 h-3" />
              {clip.duration}s
           </div>
        </div>

        {/* Bottom Play Overlay */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
           <AnimatePresence>
              {!isHovered && (
                <motion.div 
                   initial={{ opacity: 0, scale: 0.5 }}
                   animate={{ opacity: 1, scale: 1 }}
                   exit={{ opacity: 0, scale: 2 }}
                   className="w-16 h-16 bg-white/10 backdrop-blur-md rounded-full flex items-center justify-center border border-white/20"
                >
                   <Play className="w-8 h-8 text-white fill-current translate-x-0.5" />
                </motion.div>
              )}
           </AnimatePresence>
        </div>

        {/* Analysis Overlay on Hover */}
        <div className="absolute bottom-4 left-4 right-4 z-20 space-y-2 translate-y-2 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-500">
           <div className="flex gap-2 mb-4">
              <ScoreSmall icon={Target} label="Hook" score={clip.hook_score} />
              <ScoreSmall icon={Zap} label="Retention" score={clip.engagement_score} />
           </div>
           
           <div className="flex gap-2">
              <Link href={`/quick-edit/${clip.id}`} className="flex-1">
                 <Button className="w-full h-12 bg-white text-black font-extrabold hover:bg-zinc-200 rounded-2xl">
                    SỬA NHANH <Scissors className="ml-2 w-4 h-4" />
                 </Button>
              </Link>
              <Button size="icon" variant="secondary" className="w-12 h-12 rounded-2xl bg-black/50 backdrop-blur-xl border border-white/10 text-white">
                 <Download className="w-5 h-5" />
              </Button>
           </div>
        </div>
      </div>

      {/* Description Info (Below Video) */}
      <div className="p-5 border-t border-white/5">
         <h4 className="font-bold text-sm text-white/90 line-clamp-1 mb-1">
            {clip.title || `Viral Moment #${clip.id.slice(0, 4)}`}
         </h4>
         <p className="text-[10px] text-zinc-500 leading-relaxed line-clamp-2 italic">
            "{clip.reasoning || 'No reasoning available'}"
         </p>
      </div>
    </motion.div>
  )
}

function ScoreSmall({ icon: Icon, label, score }: any) {
   return (
      <div className="flex-1 bg-black/40 backdrop-blur-xl border border-white/10 rounded-xl p-2 text-center">
         <div className="flex items-center justify-center gap-1.5 mb-0.5">
            <Icon className="w-3 h-3 text-blue-400" />
            <span className="text-[8px] font-black uppercase text-zinc-400">{label}</span>
         </div>
         <span className="text-xs font-black text-white">{score}%</span>
      </div>
   )
}

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(" ")
}
