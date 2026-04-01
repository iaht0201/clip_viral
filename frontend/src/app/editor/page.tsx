"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useSession } from "@/lib/auth-client";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Slider } from "@/components/ui/slider";
import { 
  Film, 
  Search, 
  ChevronRight, 
  Languages, 
  Settings2, 
  Play, 
  Pause, 
  Type,
  FileText,
  Save,
  Wand2,
  Monitor,
  Scissors,
  Sparkles,
  Smartphone,
  Layers,
  Music,
  Download,
  Trash2,
  Undo,
  Redo,
  Layout
} from "lucide-react";
import Link from "next/link";

interface Task {
  id: string;
  source_title: string;
  source_type: string;
  status: string;
  created_at: string;
}

interface TranscriptSegment {
  text: string;
  start: number;
  end: number;
  confidence?: number;
}

interface TranscriptData {
  words: TranscriptSegment[];
  text: string;
}

export default function EditorPage() {
  const { data: session, isPending } = useSession();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [transcript, setTranscript] = useState<TranscriptData | null>(null);
  const [isLoadingTasks, setIsLoadingTasks] = useState(true);
  const [isLoadingTranscript, setIsLoadingTranscript] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [selectedSegmentIdx, setSelectedSegmentIdx] = useState<number | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  const fetchTasks = useCallback(async () => {
    try {
      setIsLoadingTasks(true);
      const response = await fetch("/api/tasks");
      if (response.ok) {
        const data = await response.json();
        setTasks(data.tasks || []);
      }
    } catch (error) {
      console.error("Failed to fetch tasks:", error);
    } finally {
      setIsLoadingTasks(false);
    }
  }, []);

  useEffect(() => {
    if (session?.user?.id) {
      fetchTasks();
    }
  }, [session?.user?.id, fetchTasks]);

  const fetchTranscript = async (taskId: string) => {
    try {
      setIsLoadingTranscript(true);
      const response = await fetch(`/api/tasks/${taskId}/transcript`);
      if (response.ok) {
        const data = await response.json();
        setTranscript(data);
      } else {
         setTranscript(null);
      }
    } catch (error) {
      setTranscript(null);
    } finally {
      setIsLoadingTranscript(false);
    }
  };

  const handleTaskSelect = (task: Task) => {
    setSelectedTaskId(task.id);
    setSelectedTask(task);
    fetchTranscript(task.id);
    if (videoRef.current) {
        videoRef.current.load();
    }
  };

  const formatTime = (seconds: number) => {
    if (isNaN(seconds)) return "00:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const seekTo = (timeMs: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = timeMs / 1000;
      if (!isPlaying) {
        videoRef.current.play();
        setIsPlaying(true);
      }
    }
  };

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const filteredTasks = tasks.filter(t => 
    t.source_title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (isPending) return null;
  if (!session?.user) return <div className="p-8 text-center">Please sign in to access the editor.</div>;

  return (
    <div className="h-screen bg-[#111] text-stone-200 flex flex-col overflow-hidden select-none">
      {/* Top Navbar */}
      <header className="h-14 bg-[#1a1a1a] border-b border-stone-800 flex items-center px-4 justify-between shrink-0">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2 font-bold text-white hover:opacity-80 transition-opacity">
            <div className="w-7 h-7 bg-white rounded flex items-center justify-center">
              <Scissors className="w-4 h-4 text-black" />
            </div>
            <span className="text-sm tracking-tight">SupoClip<span className="text-blue-500">Pro</span></span>
          </Link>
          <div className="h-4 w-[1px] bg-stone-700" />
          <nav className="flex items-center gap-4">
             <button className="text-xs font-medium hover:text-white transition-colors">Project</button>
             <button className="text-xs font-medium hover:text-white transition-colors">Edit</button>
             <button className="text-xs font-medium hover:text-white transition-colors text-blue-400">Layout</button>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center bg-[#222] rounded-md px-2 py-1 gap-4 mr-4">
             <button className="p-1 hover:bg-white/10 rounded"><Undo className="w-3.5 h-3.5" /></button>
             <button className="p-1 hover:bg-white/10 rounded"><Redo className="w-3.5 h-3.5" /></button>
          </div>
          <Button size="sm" variant="outline" className="h-8 border-stone-700 bg-transparent text-stone-300 hover:bg-white/5">
            Save
          </Button>
          <Button size="sm" className="h-8 bg-blue-600 hover:bg-blue-500 text-white font-bold px-4">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Toolbar: Assets & Library */}
        <aside className="w-64 bg-[#1a1a1a] border-r border-stone-800 flex flex-col shrink-0">
          <div className="flex border-b border-stone-800">
             <button className="flex-1 py-3 text-[11px] font-bold border-b-2 border-blue-500 text-white flex flex-col items-center gap-1">
                <Film className="w-4 h-4" /> Media
             </button>
             <button className="flex-1 py-3 text-[11px] font-bold text-stone-500 hover:text-stone-300 flex flex-col items-center gap-1">
                <Music className="w-4 h-4" /> Music
             </button>
             <button className="flex-1 py-3 text-[11px] font-bold text-stone-500 hover:text-stone-300 flex flex-col items-center gap-1">
                <Type className="w-4 h-4" /> Text
             </button>
             <button className="flex-1 py-3 text-[11px] font-bold text-stone-500 hover:text-stone-300 flex flex-col items-center gap-1">
                <Layers className="w-4 h-4" /> Stkx
             </button>
          </div>
          
          <div className="p-3">
             <div className="relative mb-3">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-stone-500" />
                <Input 
                  placeholder="Search materials..." 
                  className="h-8 pl-8 bg-[#222] border-none text-[11px] focus-visible:ring-1 focus-visible:ring-blue-500"
                />
             </div>
          </div>

          <div className="flex-1 overflow-y-auto px-2 space-y-1 custom-scrollbar">
            {isLoadingTasks ? (
                Array.from({ length: 12 }).map((_, i) => (
                  <Skeleton key={i} className="h-32 w-full bg-[#222]" />
                ))
            ) : filteredTasks.map(task => (
                <div 
                  key={task.id}
                  onClick={() => handleTaskSelect(task)}
                  className={`group relative aspect-video bg-[#222] rounded overflow-hidden cursor-pointer border-2 transition-all ${
                    selectedTaskId === task.id ? "border-blue-500" : "border-transparent hover:border-stone-600"
                  }`}
                >
                   <div className="absolute inset-0 flex items-center justify-center opacity-40">
                      <Film className="w-8 h-8" />
                   </div>
                   <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 p-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <p className="text-[10px] truncate leading-tight">{task.source_title}</p>
                   </div>
                   {selectedTaskId === task.id && (
                     <div className="absolute top-1 right-1 bg-blue-500 rounded-full p-0.5">
                        <ChevronRight className="w-2.5 h-2.5" />
                     </div>
                   )}
                </div>
            ))}
          </div>
        </aside>

        {/* Center: TikTok Preview (Vertical/Portrait) */}
        <main className="flex-1 flex flex-col bg-[#111] relative overflow-hidden">
           <div className="flex-1 flex items-center justify-center p-4 bg-grid-white/[0.02]">
              {selectedTaskId ? (
                /* TikTok Phone Frame Simulator */
                <div className="relative h-full aspect-[9/19.5] max-h-[85vh] bg-black rounded-[44px] border-8 border-[#333] shadow-2xl overflow-hidden ring-4 ring-black/40">
                   {/* Top Notch/Dynamic Island */}
                   <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1/3 h-6 bg-[#333] rounded-b-2xl z-20 flex items-center justify-center">
                      <div className="w-8 h-1.5 bg-black rounded-full" />
                   </div>

                   {/* Video Player */}
                   <video 
                      ref={videoRef}
                      className="w-full h-full object-cover"
                      onTimeUpdate={handleTimeUpdate}
                      onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
                      loop
                   >
                       <source src={`/api/tasks/${selectedTaskId}/video`} type="video/mp4" />
                   </video>

                   {/* Subtitle Overlay (Live Preview) */}
                   <div className="absolute inset-x-4 top-[60%] pointer-events-none z-30 text-center drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)]">
                      {transcript?.words.map((word, idx) => {
                         const isActive = currentTime * 1000 >= word.start && currentTime * 1000 < word.end;
                         if (!isActive) return null;
                         
                         return (
                           <div key={idx} className="animate-in fade-in zoom-in duration-300">
                             <span className="bg-yellow-400 text-black px-2 py-1 font-black italic uppercase text-lg inline-block rounded-sm transform -rotate-1 tracking-tighter">
                                {word.text}
                             </span>
                           </div>
                         );
                      })}
                   </div>

                   {/* TikTok UI Overlay Simulation */}
                   <div className="absolute inset-0 pointer-events-none z-10 flex flex-col justify-end p-4">
                      <div className="absolute right-3 bottom-32 flex flex-col items-center gap-6">
                         <div className="w-10 h-10 rounded-full border-2 border-white overflow-hidden bg-stone-800 flex items-center justify-center">
                            <span className="text-xs font-bold">👤</span>
                         </div>
                         <div className="flex flex-col items-center gap-1">
                            <div className="w-8 h-8 flex items-center justify-center text-white"><Sparkles className="w-7 h-7" /></div>
                            <span className="text-[10px] font-bold">12.4K</span>
                         </div>
                      </div>
                      <div className="mb-8 space-y-2">
                         <h4 className="text-sm font-bold text-white">@supoclip_ai</h4>
                         <p className="text-xs text-white/90 line-clamp-2">Generating viral clips automatically using AI editor... #viral #ai</p>
                         <div className="flex items-center gap-2">
                             <Music className="w-3 h-3 text-white" />
                             <span className="text-[10px] text-white">Original Sound - SupoClip</span>
                         </div>
                      </div>
                   </div>

                   {/* Video Center Play/Pause button */}
                   <button 
                     onClick={togglePlay}
                     className="absolute inset-0 flex items-center justify-center bg-black/5 opacity-0 hover:opacity-100 transition-opacity z-10 pointer-events-auto"
                   >
                      {isPlaying ? <Pause className="w-12 h-12 text-white/50" /> : <Play className="w-12 h-12 text-white/50 bg-white/10 rounded-full" />}
                   </button>
                </div>
              ) : (
                <div className="text-center space-y-4 opacity-40">
                   <div className="w-20 h-20 bg-[#222] rounded-full mx-auto flex items-center justify-center border-2 border-dashed border-stone-700">
                      <Layout className="w-8 h-8" />
                   </div>
                   <p className="text-xs font-medium uppercase tracking-widest">Select source to start</p>
                </div>
              )}
           </div>

           {/* Timeline Controls (Mini) */}
           <div className="h-10 bg-[#1a1a1a] border-t border-stone-800 flex items-center px-4 justify-between gap-10">
              <div className="flex items-center gap-4">
                 <button onClick={togglePlay} className="text-white hover:scale-110 transition-transform">
                   {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current" />}
                 </button>
                 <span className="text-[11px] font-mono tabular-nums text-stone-400">
                   {formatTime(currentTime)} / {formatTime(duration)}
                 </span>
              </div>
              
              <div className="flex-1 max-w-md flex items-center gap-3">
                 <Monitor className="w-3.5 h-3.5 text-stone-600" />
                 <Slider 
                   value={[currentTime]} 
                   max={duration || 100} 
                   step={0.1}
                   onValueChange={(val) => {if (videoRef.current) videoRef.current.currentTime = val[0]}}
                   className="flex-1"
                 />
              </div>

              <div className="flex gap-4">
                 <button className="text-stone-500 hover:text-white"><Smartphone className="w-4 h-4" /></button>
                 <button className="text-stone-500 hover:text-white"><Settings2 className="w-4 h-4" /></button>
              </div>
           </div>
        </main>

        {/* Right Sidebar: Layers & Properties */}
        <aside className="w-72 bg-[#1a1a1a] border-l border-stone-800 p-4 overflow-y-auto space-y-8">
           <section className="space-y-4">
              <h4 className="text-[10px] font-bold text-stone-500 uppercase tracking-widest border-b border-stone-800 pb-2">Properties</h4>
              
              {selectedSegmentIdx !== null && transcript ? (
                <div className="space-y-6">
                  <div className="space-y-2">
                    <label className="text-[11px] text-stone-400">Subtitle Text</label>
                    <textarea 
                       className="w-full bg-[#222] border-none rounded-md p-3 text-xs text-white min-h-[80px] focus:ring-1 focus:ring-blue-500"
                       value={transcript.words[selectedSegmentIdx].text}
                       onChange={(e) => {
                          const newWords = [...transcript.words];
                          newWords[selectedSegmentIdx].text = e.target.value;
                          setTranscript({...transcript, words: newWords});
                       }}
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                     <div className="space-y-1">
                        <label className="text-[10px] text-stone-500">Starts (ms)</label>
                        <Input 
                          type="number" 
                          className="h-8 bg-[#222] border-none text-xs" 
                          value={transcript.words[selectedSegmentIdx].start}
                          onChange={(e) => {
                             const newWords = [...transcript.words];
                             newWords[selectedSegmentIdx].start = parseInt(e.target.value);
                             setTranscript({...transcript, words: newWords});
                          }}
                        />
                     </div>
                     <div className="space-y-1">
                        <label className="text-[10px] text-stone-500">Ends (ms)</label>
                        <Input 
                          type="number" 
                          className="h-8 bg-[#222] border-none text-xs" 
                          value={transcript.words[selectedSegmentIdx].end}
                          onChange={(e) => {
                             const newWords = [...transcript.words];
                             newWords[selectedSegmentIdx].end = parseInt(e.target.value);
                             setTranscript({...transcript, words: newWords});
                          }}
                        />
                     </div>
                  </div>

                  <Separator className="bg-stone-800" />

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-stone-300">Style</label>
                    <div className="grid grid-cols-3 gap-2">
                       <button className="h-8 bg-yellow-400 rounded flex items-center justify-center border-2 border-transparent hover:border-white"></button>
                       <button className="h-8 bg-blue-500 rounded flex items-center justify-center border-2 border-transparent hover:border-white"></button>
                       <button className="h-8 bg-white rounded flex items-center justify-center border-2 border-transparent hover:border-white"></button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                   <div className="p-4 bg-white/5 rounded-lg border border-dashed border-stone-700 text-center">
                      <p className="text-[10px] text-stone-500">Click a subtitle on the timeline to edit properties.</p>
                   </div>
                   <div className="space-y-2">
                      <label className="text-[11px] text-stone-400">Project Aspect</label>
                      <Badge variant="outline" className="border-stone-700 text-stone-500">Vertical (TikTok 9:16)</Badge>
                   </div>
                </div>
              )}
           </section>

           <section className="space-y-4">
              <h4 className="text-[10px] font-bold text-stone-500 uppercase tracking-widest border-b border-stone-800 pb-2">Smart Actions</h4>
              <div className="grid gap-2">
                 <Button variant="outline" className="w-full h-8 border-stone-700 bg-transparent text-[11px] justify-start hover:bg-blue-500 hover:border-blue-500 hover:text-white transition-all">
                    <Wand2 className="w-3.5 h-3.5 mr-2" /> Auto Subtitles
                 </Button>
                 <Button variant="outline" className="w-full h-8 border-stone-700 bg-transparent text-[11px] justify-start hover:bg-amber-500 hover:border-amber-500 hover:text-white transition-all">
                    <Sparkles className="w-3.5 h-3.5 mr-2" /> AI Hook Rewrite
                 </Button>
                 <Button variant="outline" className="w-full h-8 border-stone-700 bg-transparent text-[11px] justify-start hover:bg-red-500 hover:border-red-500 hover:text-white transition-all">
                    <Trash2 className="w-3.5 h-3.5 mr-2" /> Delete All Layers
                 </Button>
              </div>
           </section>
        </aside>
      </div>

      {/* Bottom Timeline: Horizontal CapCut Style */}
      <footer className="h-64 bg-[#141414] border-t border-stone-800 flex flex-col shrink-0">
          <div className="h-8 bg-[#1a1a1a] border-b border-stone-800 flex items-center px-4 gap-6">
             <div className="flex gap-2 mr-4">
                <button className="p-1 hover:bg-white/10 rounded"><Layers className="w-4 h-4 text-stone-400" /></button>
                <button className="p-1 hover:bg-white/10 rounded"><Scissors className="w-4 h-4 text-stone-400" /></button>
             </div>
             <Separator orientation="vertical" className="h-4 bg-stone-700" />
             <div className="text-[11px] font-medium text-stone-500">Timeline: Subtitles</div>
          </div>

          <div className="flex-1 overflow-hidden relative flex">
             {/* Time Ruler */}
             <div className="absolute top-0 left-0 right-0 h-6 bg-[#1a1a1a] border-b border-stone-900 border-dashed z-10 flex items-center px-6">
                {Array.from({ length: 30 }).map((_, i) => (
                  <div key={i} className="flex-shrink-0 w-24 border-l border-stone-700 h-full text-[8px] pl-1 pt-1 text-stone-500">
                     00:{i.toString().padStart(2, '0')}s
                  </div>
                ))}
             </div>

             {/* Tracks Area */}
             <div className="flex-1 mt-6 overflow-x-auto custom-scrollbar relative">
                {/* Playhead line */}
                <div 
                   className="absolute top-0 bottom-0 w-[2px] bg-white z-20 pointer-events-none"
                   style={{ left: `${(currentTime / 30) * (30 * 96) + 24}px` }} // Assuming 96px per second
                >
                   <div className="w-3 h-3 bg-white -ml-[5px] rounded-full shadow-lg" />
                </div>

                <div className="p-4 space-y-2 min-w-[3000px]">
                   {/* Subtitle Track */}
                   <div className="h-10 bg-[#222]/30 rounded-lg relative flex items-center">
                      <div className="absolute -left-4 w-12 text-[10px] text-stone-500 origin-center -rotate-90">TEXT</div>
                      {transcript?.words.map((word, idx) => {
                         const startPx = (word.start / 1000) * 96;
                         const widthPx = ((word.end - word.start) / 1000) * 96;
                         
                         return (
                           <button 
                             key={idx}
                             onClick={() => {
                                seekTo(word.start);
                                setSelectedSegmentIdx(idx);
                             }}
                             className={`absolute h-8 rounded border border-blue-500/30 text-[10px] px-2 flex items-center truncate transition-all ${
                                (currentTime * 1000 >= word.start && currentTime * 1000 < word.end) || selectedSegmentIdx === idx
                                  ? "bg-blue-600 text-white z-10 shadow-lg scale-105"
                                  : "bg-blue-900/20 text-blue-300 hover:bg-blue-800/40"
                             } ${selectedSegmentIdx === idx ? "ring-2 ring-white" : ""}`}
                             style={{ left: `${startPx}px`, width: `${Math.max(widthPx, 20)}px` }}
                             title={word.text}
                           >
                              {word.text}
                           </button>
                         );
                      })}
                   </div>

                   {/* Background/Audio Track Wrapper */}
                   <div className="h-10 bg-emerald-900/10 rounded-lg relative flex items-center border border-emerald-900/20">
                      <div className="absolute -left-4 w-12 text-[10px] text-stone-500 origin-center -rotate-90">AUDIO</div>
                      <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/10 via-emerald-500/20 to-emerald-500/5 opacity-50" />
                   </div>
                </div>
             </div>
          </div>
      </footer>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
          height: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #111;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #333;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #444;
        }
        .bg-grid-white {
          background-size: 40px 40px;
          background-image: linear-gradient(to right, rgba(255, 255, 255, 0.05) 1px, transparent 1px),
                            linear-gradient(to bottom, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
        }
      `}</style>
    </div>
  );
}
