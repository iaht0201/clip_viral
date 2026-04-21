'use client'
import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Play, 
  Pause, 
  Maximize2, 
  Settings, 
  Volume2, 
  VolumeX, 
  RotateCcw,
  Sparkles,
  Smartphone
} from 'lucide-react'
import { Slider } from '@/components/ui/slider'

interface VerticalPlayerProps {
  videoUrl: string
  captionText?: string
  captionStyle?: {
    color: string
    fontSize: number
    fontFamily: string
    position: 'top' | 'middle' | 'bottom'
  }
}

export function VerticalPlayer({ videoUrl, captionText, captionStyle }: VerticalPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [progress, setProgress] = useState(0)
  const videoRef = useRef<HTMLVideoElement>(null)

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) videoRef.current.pause()
      else videoRef.current.play()
      setIsPlaying(!isPlaying)
    }
  }

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const p = (videoRef.current.currentTime / videoRef.current.duration) * 100
      setProgress(p)
    }
  }

  return (
    <div className="relative aspect-[9/16] bg-black rounded-[48px] overflow-hidden border-[12px] border-zinc-900 shadow-2xl shadow-blue-500/10 group select-none">
      
      {/* Video Element */}
      <video
        ref={videoRef}
        src={videoUrl}
        className="w-full h-full object-cover"
        onTimeUpdate={handleTimeUpdate}
        onClick={togglePlay}
        playsInline
      />

      {/* Dynamic Caption Overlay */}
      <AnimatePresence>
         {captionText && (
            <motion.div 
               initial={{ opacity: 0, y: 20 }}
               animate={{ opacity: 1, y: 0 }}
               exit={{ opacity: 0, scale: 0.9 }}
               className="absolute left-6 right-6 z-30 pointer-events-none text-center"
               style={{ 
                  bottom: captionStyle?.position === 'bottom' ? '20%' : captionStyle?.position === 'middle' ? '45%' : '75%',
               }}
            >
               <span 
                 className="px-4 py-2 bg-yellow-400 text-black font-black uppercase text-2xl tracking-tighter shadow-[4px_4px_0px_rgba(0,0,0,1)] rounded-lg italic"
                 style={{ 
                    color: captionStyle?.color || 'black',
                    fontSize: `${captionStyle?.fontSize || 24}px`
                 }}
               >
                 {captionText}
               </span>
            </motion.div>
         )}
      </AnimatePresence>

      {/* Top Banner (Branding) */}
      <div className="absolute top-0 left-0 right-0 p-8 pt-10 bg-gradient-to-b from-black/60 to-transparent pointer-events-none z-20">
         <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center">
               <Sparkles className="w-4 h-4 text-white fill-current" />
            </div>
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-white">ReelShort AI Studio</span>
         </div>
      </div>

      {/* Interaction Controls (Overlay on Hover) */}
      <div className="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center pointer-events-none">
         <motion.button 
            whileTap={{ scale: 0.9 }}
            onClick={togglePlay}
            className="w-20 h-20 bg-white/10 backdrop-blur-xl border border-white/20 rounded-full flex items-center justify-center text-white pointer-events-auto"
         >
            {isPlaying ? <Pause className="w-8 h-8 fill-current" /> : <Play className="w-8 h-8 fill-current translate-x-1" />}
         </motion.button>
      </div>

      {/* Bottom Controls Bar */}
      <div className="absolute bottom-0 left-0 right-0 p-8 pb-10 bg-gradient-to-t from-black/80 via-black/40 to-transparent z-20 translate-y-4 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-300">
         <div className="space-y-6">
            {/* Progress Slider */}
            <Slider 
              value={[progress]} 
              max={100} 
              step={0.1} 
              onValueChange={([val]) => {
                if (videoRef.current) {
                  videoRef.current.currentTime = (val / 100) * videoRef.current.duration
                }
              }}
              className="mt-4"
            />
            
            <div className="flex items-center justify-between">
               <div className="flex items-center gap-4">
                  <button onClick={() => setIsMuted(!isMuted)} className="text-white/80 hover:text-white transition-colors">
                     {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
                  </button>
                  <span className="text-[10px] font-mono font-bold text-white/60 tracking-widest">
                     {videoRef.current ? formatTime(videoRef.current.currentTime) : '00:00'} / {videoRef.current ? formatTime(videoRef.current.duration) : '00:00'}
                  </span>
               </div>

               <div className="flex items-center gap-4">
                  <button className="text-white/80 hover:text-white transition-colors">
                     <Settings className="w-5 h-5" />
                  </button>
                  <button className="text-white/80 hover:text-white transition-colors">
                     <Maximize2 className="w-5 h-5" />
                  </button>
               </div>
            </div>
         </div>
      </div>

      {/* Safe Area Marker */}
      <div className="absolute inset-0 border border-white/5 pointer-events-none m-8 rounded-[32px] opacity-20 border-dashed" />
      
      {/* Device Indicator */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 w-20 h-1 bg-white/20 rounded-full" />
    </div>
  )
}

function formatTime(seconds: number) {
  if (isNaN(seconds)) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}
