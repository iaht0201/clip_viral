'use client'
import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Upload, 
  Youtube, 
  PlaySquare, 
  Link as LinkIcon, 
  FileVideo,
  Sparkles,
  ArrowRight
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface DropzoneProps {
  onAnalyze: (url: string) => void
}

export function Dropzone({ onAnalyze }: DropzoneProps) {
  const [url, setUrl] = useState('')
  const [isUrlMode, setIsUrlMode] = useState(true)

  const handleAnalyze = () => {
    if (url.trim()) {
      onAnalyze(url)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative group mt-8"
    >
      <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-purple-600 rounded-[32px] blur opacity-20 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
      
      <div className="relative border border-white/5 rounded-[32px] p-12 lg:p-16 text-center bg-zinc-900/40 backdrop-blur-3xl overflow-hidden min-h-[400px] flex flex-col items-center justify-center">
        
        {/* Background Sparkles */}
        <div className="absolute top-0 left-0 w-full h-full pointer-events-none opacity-20">
          <div className="absolute top-10 left-10 w-32 h-32 bg-blue-500/20 blur-3xl rounded-full" />
          <div className="absolute bottom-10 right-10 w-32 h-32 bg-purple-500/20 blur-3xl rounded-full" />
        </div>

        <motion.div 
          whileHover={{ scale: 1.05, rotate: 5 }}
          className="mx-auto w-24 h-24 bg-gradient-to-br from-zinc-800 to-zinc-900 border border-white/10 rounded-3xl flex items-center justify-center mb-10 shadow-2xl relative"
        >
          <div className="absolute -inset-2 bg-blue-500/10 blur-xl rounded-full animate-pulse" />
          <Upload className="w-12 h-12 text-blue-400 relative z-10" />
        </motion.div>

        <h3 className="text-4xl font-extrabold mb-4 tracking-tight">
          Thả link hoặc upload video
        </h3>
        <p className="text-zinc-400 mb-12 text-lg font-medium max-w-md mx-auto">
          AI của chúng tôi sẽ tự động đề xuất những khoảnh khắc có tiềm năng Viral cao nhất.
        </p>

        <div className="w-full max-w-2xl mx-auto space-y-6">
          <div className="flex gap-3 items-center group/input relative">
            <div className="absolute left-6 text-zinc-500 group-focus-within/input:text-blue-400 transition-colors">
              <LinkIcon className="w-5 h-5" />
            </div>
            <input
              type="text"
              placeholder="Dán link YouTube, Bilibili, TikTok..."
              className="w-full bg-black/40 border border-white/5 rounded-2xl pl-16 pr-6 py-5 text-lg outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500/50 transition-all placeholder:text-zinc-700 shadow-inner"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
            />
            <Button
              onClick={handleAnalyze}
              disabled={!url.trim()}
              className="absolute right-2 px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-bold rounded-xl shadow-lg shadow-blue-500/20 group-hover:scale-[1.02] transition-all disabled:opacity-50 disabled:grayscale"
            >
              Phân tích AI <ArrowRight className="ml-2 w-4 h-4" />
            </Button>
          </div>

          <div className="flex flex-wrap justify-center gap-6 text-xs font-bold text-zinc-500 uppercase tracking-widest pt-4">
            <div className="flex items-center gap-2 px-3 py-1.5 hover:text-white transition-colors cursor-default">
              <Youtube className="w-4 h-4 text-red-500" /> YouTube
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 hover:text-white transition-colors cursor-default">
              <PlaySquare className="w-4 h-4 text-blue-400" /> Bilibili
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 hover:text-white transition-colors cursor-default">
              <Sparkles className="w-4 h-4 text-purple-400" /> TikTok
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 hover:text-white transition-colors cursor-default underline decoration-zinc-700">
              <FileVideo className="w-4 h-4" /> MP4 Upload
            </div>
          </div>
        </div>

        {/* Floating badge */}
        <div className="absolute top-8 right-8">
           <div className="px-3 py-1 bg-white/5 border border-white/5 rounded-full flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
              <span className="text-[10px] font-bold text-zinc-400 uppercase">GPU Engine Active</span>
           </div>
        </div>
      </div>
    </motion.div>
  )
}
