'use client'
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useParams, useRouter } from 'next/navigation'
import { 
  ArrowLeft, 
  Save, 
  Download, 
  Scissors, 
  Type, 
  Mic2, 
  Wand2, 
  Music,
  Share2,
  Sparkles,
  Zap,
  ArrowRight,
  Loader2,
  AlertCircle
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { VerticalPlayer } from '@/components/shared/VerticalPlayer'

export default function QuickEditPage() {
  const { clipId } = useParams()
  const router = useRouter()
  const [clip, setClip] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const [isSaving, setIsSaving] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [isDubbing, setIsDubbing] = useState(false)

  const [captionText, setCaptionText] = useState('ĐÂY LÀ KHOẢNH KHẮC VIRAL!')
  const [captionStyle, setCaptionStyle] = useState<{
    color: string
    fontSize: number
    fontFamily: string
    position: 'top' | 'middle' | 'bottom'
  }>({
     color: '#FFD700',
     fontSize: 28,
     fontFamily: 'Syne',
     position: 'bottom'
  })

  useEffect(() => {
    const fetchClip = async () => {
      if (!clipId) return
      
      try {
        const res = await fetch(`http://localhost:8000/tasks/clips/${clipId}`, {
           headers: { "user_id": "local_user" }
        })
        if (!res.ok) throw new Error("Could not find clip metadata")
        const data = await res.json()
        
        // Ensure full URL for player
        if (data.video_url && !data.video_url.startsWith('http')) {
           data.video_url = `http://localhost:8000${data.video_url}`
        }
        
        setClip(data)
        if (data.text) setCaptionText(data.text)
        if (data.position) setCaptionStyle(s => ({...s, position: data.position}))
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    
    fetchClip()
  }, [clipId])

  const handleSave = async () => {
    if (!clip) return
    setIsSaving(true)
    try {
      const res = await fetch(`http://localhost:8000/tasks/${clip.task_id}/clips/${clipId}/captions`, {
        method: 'PATCH',
        headers: { 
          'Content-Type': 'application/json',
          'user_id': 'local_user'
        },
        body: JSON.stringify({
          caption_text: captionText,
          position: captionStyle.position,
          highlight_words: [] // For now empty, can be improved
        })
      })
      if (!res.ok) throw new Error("Failed to save captions")
      const data = await res.json()
      
      // Update local clip but keep current video_url if not changed
      // Actually backend might have regenerated the file, so we should update
      if (data.clip?.video_url) {
        const newUrl = data.clip.video_url.startsWith('http') 
          ? data.clip.video_url 
          : `http://localhost:8000${data.clip.video_url}`
        setClip({...data.clip, video_url: newUrl})
      }
      
      alert("Project Saved Successfully!")
    } catch (err: any) {
      alert("Error saving: " + err.message)
    } finally {
      setIsSaving(false)
    }
  }

  const handleExport = async () => {
    if (!clip) return
    setIsExporting(true)
    try {
      const url = `http://localhost:8000/tasks/${clip.task_id}/clips/${clipId}/export?preset=tiktok`
      // Use clean hidden link for reliable download
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `supoclip_${clipId}_tiktok.mp4`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err: any) {
      alert("Export failed: " + err.message)
    } finally {
      setTimeout(() => setIsExporting(false), 2000)
    }
  }

  const handleDubbing = async () => {
     if (!clip) return
     setIsDubbing(true)
     try {
       const res = await fetch(`http://localhost:8000/tasks/${clip.task_id}/clips/${clipId}/dub`, {
         method: 'POST',
         headers: { 
           'Content-Type': 'application/json',
           'user_id': 'local_user'
         },
         body: JSON.stringify({
           text: captionText,
           voice: "vi-VN-HoaiMyNeural" // Female voice for dubbing
         })
       })
       if (!res.ok) throw new Error("Dubbing failed")
       const data = await res.json()
       
       if (data.clip?.video_url) {
         const newUrl = data.clip.video_url.startsWith('http') 
           ? data.clip.video_url 
           : `http://localhost:8000${data.clip.video_url}`
         setClip({...data.clip, video_url: newUrl})
       }
       alert("Dubbing Complete! Audio has been replaced.")
     } catch (err: any) {
       alert("Dubbing failed: " + err.message)
     } finally {
       setIsDubbing(false)
     }
  }

  if (loading) {
     return (
        <div className="h-screen flex flex-col items-center justify-center bg-black gap-6">
           <Loader2 className="w-12 h-12 animate-spin text-blue-500" />
           <p className="text-zinc-500 font-bold uppercase tracking-widest animate-pulse">Loading Studio...</p>
        </div>
     )
  }

  if (error || !clip) {
     return (
        <div className="h-screen flex flex-col items-center justify-center bg-black p-10 text-center">
           <AlertCircle className="w-20 h-20 text-red-500 mb-8" />
           <h2 className="text-3xl font-black mb-4 uppercase italic">Clip Not Found</h2>
           <p className="text-zinc-500 mb-10 max-w-sm">{error || "The clip you are looking for might have been deleted or moved."}</p>
           <Button onClick={() => router.back()} variant="outline" className="h-14 px-10 rounded-2xl border-white/10 hover:bg-white/5">
               GO BACK
           </Button>
        </div>
     )
  }

  return (
    <div className="h-full flex flex-col overflow-hidden bg-black">
      
      {/* Top Header Bar */}
      <header className="h-16 border-b border-white/5 bg-zinc-950 flex items-center justify-between px-6 shrink-0">
        <div className="flex items-center gap-6">
           <button 
             onClick={() => router.back()} 
             className="flex items-center gap-2 text-zinc-500 hover:text-white transition-colors text-xs font-bold uppercase tracking-widest group"
           >
              <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" /> Back
           </button>
           <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center">
                 <Scissors className="w-4 h-4 text-white fill-current" />
              </div>
              <h1 className="text-sm font-black text-white/90 uppercase tracking-widest">
                 Quick Edit Studio — <span className="text-zinc-500 font-mono">#{clipId?.slice(0,8)}</span>
              </h1>
           </div>
        </div>

        <div className="flex items-center gap-3">
           <Button variant="ghost" className="h-10 px-4 rounded-xl text-zinc-400 hover:text-white hover:bg-white/5">
              <Share2 className="mr-2 w-4 h-4" /> Share
           </Button>
           <Button 
             onClick={handleSave}
             disabled={isSaving}
             className="h-10 px-6 rounded-xl bg-blue-500 hover:bg-blue-600 text-white font-bold"
           >
              {isSaving ? <Loader2 className="mr-2 w-4 h-4 animate-spin" /> : <Save className="mr-2 w-4 h-4" />} 
              Save Project
           </Button>
           <Button 
             onClick={handleExport}
             disabled={isExporting}
             className="h-10 px-6 rounded-xl bg-white text-black font-black hover:bg-zinc-200"
           >
              {isExporting ? <Loader2 className="mr-2 w-4 h-4 animate-spin" /> : <Download className="mr-2 w-4 h-4" />} 
              EXPORT VIDEO
           </Button>
        </div>
      </header>

      {/* Main Split Body */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Left Side: Vertical Player (40%) */}
        <section className="w-full lg:w-[40%] flex flex-col items-center justify-center p-8 bg-zinc-950/50 relative overflow-hidden">
           {/* Background Glow */}
           <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-blue-500/5 blur-[120px] rounded-full pointer-events-none" />
           
           <div className="relative w-full max-w-[360px] animate-in fade-in zoom-in duration-700">
              <VerticalPlayer 
                videoUrl={clip?.video_url} 
                captionText={captionText}
                captionStyle={captionStyle}
              />
               <p className="mt-4 text-[8px] font-mono text-zinc-700 truncate text-center" title={clip?.video_url}>
                  SRC: {clip?.video_url}
               </p>
              
              {/* Floating Virality Badge */}
              <div className="absolute -right-12 top-20 z-50">
                 <motion.div 
                   animate={{ y: [0, -10, 0] }}
                   transition={{ duration: 3, repeat: Infinity }}
                   className="bg-zinc-900 border border-white/10 rounded-2xl p-4 shadow-2xl flex flex-col items-center gap-1"
                 >
                    <span className="text-[10px] font-black text-orange-500 uppercase">Viral Score</span>
                    <span className="text-2xl font-black text-white">{clip?.virality_score} 🔥</span>
                 </motion.div>
              </div>
           </div>
        </section>

        {/* Right Side: Tools & Tabs (60%) */}
        <section className="flex-1 border-l border-white/5 bg-zinc-950 flex flex-col">
           <Tabs defaultValue="style" className="flex-1 flex flex-col">
              <div className="px-8 pt-8 shrink-0">
                 <TabsList className="bg-white/5 border border-white/5 h-16 rounded-3xl p-1 gap-1">
                    <TabsTrigger value="script" className="flex-1 rounded-2xl data-[state=active]:bg-zinc-900 data-[state=active]:text-blue-400 font-bold uppercase text-[10px] tracking-widest gap-2">
                       <Mic2 className="w-4 h-4" /> Script & Dub
                    </TabsTrigger>
                    <TabsTrigger value="style" className="flex-1 rounded-2xl data-[state=active]:bg-zinc-900 data-[state=active]:text-blue-400 font-bold uppercase text-[10px] tracking-widest gap-2">
                       <Type className="w-4 h-4" /> Caption Style
                    </TabsTrigger>
                    <TabsTrigger value="effects" className="flex-1 rounded-2xl data-[state=active]:bg-zinc-900 data-[state=active]:text-purple-400 font-bold uppercase text-[10px] tracking-widest gap-2">
                       <Wand2 className="w-4 h-4" /> AI Effects
                    </TabsTrigger>
                    <TabsTrigger value="music" className="flex-1 rounded-2xl data-[state=active]:bg-zinc-900 data-[state=active]:text-pink-400 font-bold uppercase text-[10px] tracking-widest gap-2">
                       <Music className="w-4 h-4" /> Music
                    </TabsTrigger>
                 </TabsList>
              </div>

              <div className="flex-1 overflow-y-auto custom-scrollbar p-8">
                 <TabsContent value="style" className="m-0 space-y-10">
                    <div>
                       <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                          <Type className="w-5 h-5 text-blue-400" /> Caption Text Content
                       </h3>
                       <textarea 
                          value={captionText}
                          onChange={(e) => setCaptionText(e.target.value)}
                          className="w-full bg-white/5 border border-white/5 rounded-2xl p-6 text-xl font-bold italic h-32 focus:border-blue-500/50 outline-none transition-all"
                       />
                    </div>

                    <div className="grid grid-cols-2 gap-8">
                       <div>
                          <h4 className="text-xs font-black text-zinc-500 uppercase tracking-widest mb-4">Preset Styles</h4>
                          <div className="grid grid-cols-2 gap-3">
                           <StyleButton label="Dynamic Viral" active={captionStyle.fontSize === 28} onClick={() => setCaptionStyle(s => ({...s, fontSize: 28}))} />
                             <StyleButton label="Minimalist" active={captionStyle.fontSize === 24} onClick={() => setCaptionStyle(s => ({...s, fontSize: 24}))} />
                             <StyleButton label="Alex Hormozi" active={captionStyle.color === '#FFD700' && captionStyle.fontSize === 32} onClick={() => setCaptionStyle(s => ({...s, color: '#FFD700', fontSize: 32}))} />
                             <StyleButton label="Cinematic" active={captionStyle.fontSize === 20} onClick={() => setCaptionStyle(s => ({...s, fontSize: 20}))} />
                          </div>
                       </div>
                       <div>
                          <h4 className="text-xs font-black text-zinc-500 uppercase tracking-widest mb-4">Color Palette</h4>
                          <div className="flex gap-4">
                             <ColorDot color="#FFD700" active={captionStyle.color === '#FFD700'} onClick={() => setCaptionStyle(s => ({...s, color: '#FFD700'}))} />
                             <ColorDot color="#FFFFFF" active={captionStyle.color === '#FFFFFF'} onClick={() => setCaptionStyle(s => ({...s, color: '#FFFFFF'}))} />
                             <ColorDot color="#3b82f6" active={captionStyle.color === '#3b82f6'} onClick={() => setCaptionStyle(s => ({...s, color: '#3b82f6'}))} />
                             <ColorDot color="#ef4444" active={captionStyle.color === '#ef4444'} onClick={() => setCaptionStyle(s => ({...s, color: '#ef4444'}))} />
                          </div>
                       </div>
                    </div>

                    <div>
                       <h4 className="text-xs font-black text-zinc-500 uppercase tracking-widest mb-4">Positioning</h4>
                       <div className="flex gap-3">
                          <Button 
                             onClick={() => setCaptionStyle(s => ({...s, position: 'top'}))}
                             variant={captionStyle.position === 'top' ? 'default' : 'outline'}
                             className="flex-1 rounded-2xl h-14"
                          >Top</Button>
                          <Button 
                             onClick={() => setCaptionStyle(s => ({...s, position: 'middle'}))}
                             variant={captionStyle.position === 'middle' ? 'default' : 'outline'}
                             className="flex-1 rounded-2xl h-14"
                          >Middle</Button>
                          <Button 
                             onClick={() => setCaptionStyle(s => ({...s, position: 'bottom'}))}
                             variant={captionStyle.position === 'bottom' ? 'default' : 'outline'}
                             className="flex-1 rounded-2xl h-14"
                          >Bottom (Safe Area)</Button>
                       </div>
                    </div>
                 </TabsContent>

                 <TabsContent value="script" className="m-0 space-y-8">
                    <div className="p-8 bg-zinc-900 rounded-3xl border border-white/5 border-dashed flex flex-col items-center justify-center text-center">
                       <Zap className="w-12 h-12 text-blue-500 mb-4 animate-pulse" />
                       <h4 className="text-xl font-bold mb-2">Word-Level Dubbing</h4>
                       <p className="text-zinc-500 max-w-sm mb-6">Chỉnh sửa lời thoại và AI MeloTTS sẽ tự động tạo giọng nói tiếng Việt tự nhiên nhất.</p>
                        <Button 
                          onClick={handleDubbing}
                          disabled={isDubbing}
                          className="rounded-xl px-10"
                        >
                           {isDubbing ? <Loader2 className="mr-2 w-4 h-4 animate-spin" /> : <Zap className="mr-2 w-4 h-4" />}
                           Kích hoạt Dubbing Studio
                        </Button>
                    </div>
                 </TabsContent>
              </div>

              {/* Bottom Sticky Action */}
              <div className="p-8 border-t border-white/5 bg-zinc-950/80 backdrop-blur-xl shrink-0">
                 <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                       <div className="p-2 bg-green-500/10 rounded-full">
                          <Sparkles className="w-4 h-4 text-green-500" />
                       </div>
                       <span className="text-xs font-bold text-zinc-400">AI đã tối ưu hóa bố cục Video</span>
                    </div>
                    <Button size="lg" className="rounded-2xl h-16 px-12 bg-gradient-to-r from-blue-500 to-purple-600 hover:brightness-110 font-black text-lg group">
                       XỨ TRÌNH VIDEO NGAY TIẾP THEO <ArrowRight className="ml-3 w-6 h-6 border-2 border-white/20 rounded-full p-1 group-hover:translate-x-1 transition-transform" />
                    </Button>
                 </div>
              </div>
           </Tabs>
        </section>
      </div>
    </div>
  )
}

function StyleButton({ label, active, onClick }: any) {
  return (
    <button 
      onClick={onClick}
      className={cn(
       "h-14 rounded-2xl border px-4 text-xs font-bold transition-all",
       active ? "bg-white text-black border-white" : "bg-transparent border-white/10 text-zinc-500 hover:border-white/30"
    )}>
       {label}
    </button>
  )
}

function ColorDot({ color, active, onClick }: any) {
  return (
    <button 
      onClick={onClick}
      className={cn(
        "w-10 h-10 rounded-full border-2 transition-all hover:scale-110",
        active ? "border-blue-500 scale-110 p-0.5" : "border-transparent"
      )}
    >
       <div className="w-full h-full rounded-full" style={{ backgroundColor: color }} />
    </button>
  )
}

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(" ")
}
