"use client";

import { useState, useRef, useEffect } from "react";
import { useSession } from "@/lib/auth-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  Plus, 
  LayoutDashboard, 
  Languages, 
  Scissors, 
  Library, 
  LayoutTemplate, 
  BarChart3, 
  Settings,
  Bell,
  Search,
  Youtube,
  CloudUpload,
  Zap,
  ArrowRight,
  Clock,
  Sparkles,
  Smartphone,
  ChevronRight,
  Monitor
} from "lucide-react";
import Link from "next/link";
import Image from "next/image";

export default function HomePage() {
  const { data: session, isPending } = useSession();
  const [url, setUrl] = useState("");
  const [isFastMode, setIsFastMode] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [taskStatus, setTaskStatus] = useState<any>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [generatedClips, setGeneratedClips] = useState<any[]>([]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Real-time SSE listener for task status
  useEffect(() => {
    let eventSource: EventSource | null = null;
    if (isAnalyzing && taskStatus?.task_id) {
       const userId = session?.user?.id || "local_user";
       eventSource = new EventSource(`http://localhost:8000/tasks/${taskStatus.task_id}/progress?user_id=${userId}`);
       
       eventSource.onmessage = (event) => {
          const data = JSON.parse(event.data);
          setTaskStatus((prev: any) => ({ ...prev, ...data }));
          
          if (data.status === "completed") {
             setIsAnalyzing(false);
             fetchClips(taskStatus.task_id);
             eventSource?.close();
          }
          
          const newLog = getLogForStatus(data.status?.toUpperCase(), data.progress);
          if (newLog && !logs.includes(newLog)) {
             setLogs(prev => [...prev.slice(-10), newLog]);
          }
       };

       eventSource.addEventListener("status", (event: any) => {
          const data = JSON.parse(event.data);
          setTaskStatus((prev: any) => ({ ...prev, ...data }));
          if (data.status === "completed") {
             setIsAnalyzing(false);
             fetchClips(taskStatus.task_id);
             eventSource?.close();
          }
       });

       eventSource.onerror = (err) => {
          console.error("SSE Error:", err);
          eventSource?.close();
       };
    }
    return () => eventSource?.close();
  }, [isAnalyzing, taskStatus?.task_id, logs, session?.user?.id]);

  const getLogForStatus = (status: string, progress: number) => {
    if (status === "QUEUED") return "[SYSTEM] Task queued in Redis...";
    if (status === "PROCESSING") {
      if (progress < 30) return `[DOWNLOAD] Fetching video assets... ${progress}%`;
      if (progress < 60) return `[AI] Transcribing audio with word-level precision... ${progress}%`;
      return `[AI] Analyzing virality with Llama 3... ${progress}%`;
    }
    if (status === "COMPLETED") return "✅ Task completed! Generating clips gallery...";
    return null;
  };

  const handleStartAnalysis = async () => {
    if (!url) return;
    setIsAnalyzing(true);
    setLogs(["[SYSTEM] Initializing ReelsShort AI Engine...", "[API] Creating task for URL..."]);
    
    try {
      const res = await fetch("http://localhost:8000/tasks/create/clips", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "user_id": session?.user?.id || "local_user"
        },
        body: JSON.stringify({
          source: { url: url },
          processing_mode: isFastMode ? "fast" : "full",
          task_mode: "clips"
        })
      });
      const data = await res.json();
      if (data.task_id) {
        setTaskStatus({ task_id: data.task_id, status: "QUEUED", progress: 0 });
      } else {
        throw new Error("No task ID returned");
      }
    } catch (err) {
      console.error("Task creation failed:", err);
      setIsAnalyzing(false);
      alert("Lỗi khi tạo nhiệm vụ. Vui lòng kiểm tra lại Backend!");
    }
  };

  const fetchClips = async (taskId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/tasks/${taskId}/clips`, {
        headers: { "user_id": session?.user?.id || "local_user" }
      });
      const data = await res.json();
      setGeneratedClips(data.clips || []);
    } catch (err) {
      console.error("Error fetching clips:", err);
    }
  };

  if (isPending || !mounted) return null;

  // Render Landing Page if not logged in
  if (!session?.user) {
    return (
      <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-6 text-center space-y-8 animate-in fade-in duration-700">
         <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-full blur opacity-40 group-hover:opacity-75 transition duration-1000"></div>
            <div className="relative bg-black px-8 py-3 rounded-full flex items-center gap-3 border border-white/10">
               <Zap className="w-6 h-6 text-cyan-400 fill-cyan-400" />
               <span className="text-2xl font-black tracking-tighter">REELSHORT AI</span>
            </div>
         </div>
         <h1 className="text-5xl md:text-7xl font-black tracking-tighter max-w-4xl leading-tight">
            Biến video dài thành <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500">triệu view</span> chỉ với 1 click.
         </h1>
         <p className="text-stone-400 text-lg max-w-xl">
            Sử dụng AI tiên tiến nhất để bóc tách clip, lồng tiếng Việt (MeloTTS) và tự động căn chỉnh khung hình TikTok/Reels.
         </p>
         <Button size="lg" className="h-14 px-10 bg-white text-black hover:bg-stone-200 rounded-full font-bold text-lg shadow-[0_0_30px_rgba(255,255,255,0.2)]">
            Bắt đầu miễn phí ngay
         </Button>
         <div className="pt-20 grid grid-cols-2 md:grid-cols-4 gap-8 opacity-40 grayscale group-hover:grayscale-0 transition-all">
            <div className="flex items-center gap-2"><Youtube /> YouTube</div>
            <div className="font-bold tracking-widest text-xl">Bilibili</div>
            <div className="font-bold tracking-widest text-xl">Douyin</div>
            <div className="font-bold tracking-widest text-xl">TikTok</div>
         </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-[#050505] text-stone-200 overflow-hidden font-sans">
      {/* 1. Left Sidebar (Fixed) */}
      <aside className="w-64 bg-[#0a0a0a] border-r border-white/5 flex flex-col shrink-0">
        <div className="p-6">
           <div className="flex items-center gap-2 mb-8">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-purple-600 flex items-center justify-center">
                 <Zap className="w-5 h-5 text-white fill-white" />
              </div>
              <span className="font-black text-white tracking-tighter text-xl">ReelShort AI</span>
           </div>
           
           <Button className="w-full h-11 bg-white text-black hover:bg-stone-200 rounded-xl font-bold gap-2 mb-6 shadow-lg shadow-white/5">
              <Plus className="w-4 h-4" /> New Project
           </Button>

           <nav className="space-y-1">
              {[
                { icon: LayoutDashboard, label: "AI Studio", active: true },
                { icon: Languages, label: "Dubbing Center" },
                { icon: Scissors, label: "Pro Editor" },
                { icon: Library, label: "My Library" },
                { icon: LayoutTemplate, label: "Templates" },
                { icon: BarChart3, label: "Analytics" },
              ].map((item, i) => (
                <button 
                  key={i}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all group ${
                    item.active 
                      ? "bg-white/5 text-cyan-400 border border-cyan-400/20" 
                      : "text-stone-500 hover:text-stone-300 hover:bg-white/[0.02]"
                  }`}
                >
                  <item.icon className={`w-4 h-4 ${item.active ? "text-cyan-400" : "group-hover:text-stone-300"}`} />
                  {item.label}
                </button>
              ))}
           </nav>
        </div>

        <div className="mt-auto p-6 space-y-4">
           <div className="bg-gradient-to-br from-cyan-900/20 to-purple-900/20 border border-white/5 rounded-2xl p-4">
              <p className="text-[10px] font-bold text-stone-500 uppercase tracking-widest mb-2">My Plan</p>
              <div className="flex justify-between items-center mb-1">
                 <span className="text-xs font-bold text-white">Free Trial</span>
                 <span className="text-[10px] text-stone-400">12/30 mins</span>
              </div>
              <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                 <div className="h-full bg-gradient-to-r from-cyan-400 to-purple-500 w-[40%]"></div>
              </div>
           </div>
           
           <button className="w-full flex items-center gap-3 px-4 py-2 text-stone-500 hover:text-stone-300 text-sm">
              <Settings className="w-4 h-4" /> Settings
           </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* 2. Top Bar */}
        <header className="h-16 border-b border-white/5 bg-[#050505]/80 backdrop-blur-xl flex items-center px-8 justify-between shrink-0 z-10">
           <div className="flex-1 max-w-2xl relative group">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-500 group-focus-within:text-cyan-400 transition-colors" />
              <Input 
                placeholder="Dán link video từ YouTube, Bilibili, Douyin..." 
                className="h-11 bg-white/5 border-none rounded-2xl pl-12 pr-4 text-sm focus-visible:ring-1 focus-visible:ring-cyan-400/50"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
           </div>

           <div className="flex items-center gap-4">
              <button className="flex items-center gap-2 h-10 px-4 bg-white/5 rounded-xl border border-white/5 hover:bg-white/[0.08] transition-colors">
                 <CloudUpload className="w-4 h-4 text-cyan-400" />
                 <span className="text-xs font-bold">Upload MP4</span>
              </button>
              
              <div className="h-4 w-[1px] bg-white/10 mx-2" />
              
              <button className="p-2.5 rounded-full bg-white/5 hover:bg-white/[0.08] border border-white/5 text-stone-400 relative">
                 <Bell className="w-5 h-5" />
                 <div className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-black"></div>
              </button>

              <div className="w-10 h-10 rounded-full border-2 border-white/10 bg-gradient-to-br from-stone-800 to-black overflow-hidden ring-4 ring-black">
                 <Image src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${session.user.name}`} alt="Avatar" width={40} height={40} />
              </div>
           </div>
        </header>

        {/* 3. Dashboard Body */}
        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar relative">
           {/* Processing Screen Overlay */}
           {isAnalyzing && (
             <div className="absolute inset-0 z-50 bg-[#050505]/95 backdrop-blur-2xl p-12 flex flex-col items-center justify-center animate-in fade-in zoom-in duration-500 overflow-hidden">
                <div className="max-w-5xl w-full grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
                   {/* Left: Circular Progress */}
                   <div className="flex flex-col items-center space-y-8">
                      <div className="relative w-64 h-64 flex items-center justify-center">
                         {/* Outer Glow Ring */}
                         <div className="absolute inset-0 rounded-full border border-white/5 shadow-[0_0_50px_rgba(34,211,238,0.1)]"></div>
                         
                         {/* Progress Circle (SVG) */}
                         <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 100 100">
                            <circle 
                               cx="50" cy="50" r="45" 
                               className="stroke-white/5 fill-none" 
                               strokeWidth="6" 
                            />
                            <circle 
                               cx="50" cy="50" r="45" 
                               className="stroke-cyan-400 fill-none transition-all duration-1000 ease-out" 
                               strokeWidth="6" 
                               strokeDasharray="283"
                               strokeDashoffset={283 - (283 * (taskStatus?.progress || 0)) / 100}
                               strokeLinecap="round"
                            />
                         </svg>
                         
                         {/* Percentage Text */}
                         <div className="absolute inset-x-0 inset-y-0 flex flex-col items-center justify-center">
                            <span className="text-6xl font-black text-white tracking-tighter">{taskStatus?.progress || 0}%</span>
                            <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-widest mt-2">{taskStatus?.status || "Analyzing"}</span>
                         </div>
                      </div>

                      {/* Stage Grid */}
                      <div className="w-full space-y-4 max-w-sm">
                         {[
                            { label: "Download & Ingest", value: (taskStatus?.progress || 0) > 30 ? 100 : ((taskStatus?.progress || 0) * 3.3).toFixed(0), active: (taskStatus?.progress || 0) <= 30, done: (taskStatus?.progress || 0) > 30 },
                            { label: "Transcription (Word-level)", value: (taskStatus?.progress || 0) > 60 ? 100 : (taskStatus?.progress || 0) > 30 ? (((taskStatus?.progress || 0) - 30) * 3.3).toFixed(0) : 0, active: (taskStatus?.progress || 0) > 30 && (taskStatus?.progress || 0) <= 60, done: (taskStatus?.progress || 0) > 60 },
                            { label: "AI Analysis (Llama 3)", value: (taskStatus?.progress || 0) > 90 ? 100 : (taskStatus?.progress || 0) > 60 ? (((taskStatus?.progress || 0) - 60) * 3.3).toFixed(0) : 0, active: (taskStatus?.progress || 0) > 60 && (taskStatus?.progress || 0) <= 90, done: (taskStatus?.progress || 0) > 90 },
                            { label: "Viral Clipping & Score", value: taskStatus?.status === "COMPLETED" ? 100 : 0, active: (taskStatus?.progress || 0) > 90, done: taskStatus?.status === "COMPLETED" },
                         ].map((stage, i) => (
                            <div key={i} className="space-y-1.5 opacity-90">
                               <div className="flex justify-between items-center px-1">
                                  <span className={`text-[11px] font-bold ${stage.done ? "text-green-500" : stage.active ? "text-cyan-400" : "text-stone-500"}`}>
                                     {stage.label}
                                  </span>
                                  <span className="text-[10px] font-mono text-stone-400">{stage.value}%</span>
                               </div>
                               <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                                  <div 
                                    className={`h-full transition-all duration-1000 ${stage.done ? "bg-green-500" : stage.active ? "bg-cyan-400" : "bg-stone-800"}`} 
                                    style={{ width: `${stage.value}%` }} 
                                  />
                               </div>
                            </div>
                         ))}
                      </div>
                   </div>

                   {/* Right: Live Log Console */}
                   <div className="bg-[#0a0a0a] border border-white/5 rounded-3xl p-6 h-[400px] flex flex-col shadow-2xl relative overflow-hidden group">
                      <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-4">
                         <h4 className="text-xs font-bold text-white uppercase tracking-widest">Live Process Log</h4>
                         <div className="flex gap-1.5">
                            <div className="w-2 h-2 rounded-full bg-red-500/50"></div>
                            <div className="w-2 h-2 rounded-full bg-amber-500/50"></div>
                            <div className="w-2 h-2 rounded-full bg-green-500/50"></div>
                         </div>
                      </div>

                      <div className="flex-1 overflow-y-auto custom-scrollbar font-mono text-[10px] space-y-3 pr-2 select-text text-left">
                         {logs.map((log, i) => (
                            <p key={i} className={log.includes("✅") ? "text-green-500" : "text-stone-400"}>
                               {log}
                            </p>
                         ))}
                      </div>

                      {/* Bottom Info */}
                      <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between opacity-60">
                         <span className="text-[9px] uppercase tracking-widest">Est. remaining: 2m 14s</span>
                         <span className="text-[9px] uppercase tracking-widest">SupoClip Core v2.4</span>
                      </div>
                   </div>
                </div>

                {/* Footer Actions */}
                <div className="mt-16 flex items-center gap-6">
                   <Button 
                     variant="outline" 
                     className="h-11 border-white/10 bg-white/5 text-white hover:bg-red-500/10 hover:text-red-500 rounded-xl px-10 font-bold"
                     onClick={() => setIsAnalyzing(false)}
                   >
                      Hủy bỏ
                   </Button>
                   <Button 
                     className="h-11 bg-white text-black hover:bg-stone-200 rounded-xl px-10 font-black shadow-[0_0_40px_rgba(255,255,255,0.1)]"
                     onClick={() => setIsAnalyzing(false)}
                   >
                      Chạy nền &amp; Thông báo Telegram
                   </Button>
                </div>
             </div>
           )}
           {/* Hero Dropzone Card */}
           <div className="relative group mb-12">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-[32px] blur-lg opacity-20 group-hover:opacity-40 transition duration-1000"></div>
              <Card className="relative bg-[#0a0a0a] border-white/5 rounded-[32px] p-12 overflow-hidden flex flex-col items-center text-center space-y-8">
                 <div className="absolute top-0 right-0 p-8 opacity-5">
                    <Zap className="w-64 h-64 text-white" />
                 </div>

                 <div className="space-y-2">
                    <h2 className="text-4xl font-black text-white tracking-tighter">AI CONTENT STUDIO</h2>
                    <p className="text-stone-500 text-sm">Thả link video hoặc tải tệp lên để bắt đầu tạo clip viral</p>
                 </div>

                 <div className="flex flex-wrap items-center justify-center gap-4 opacity-70">
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-red-500/10 text-red-500 rounded-lg border border-red-500/20">
                       <Youtube className="w-4 h-4" /> <span className="text-[10px] font-bold">YouTube</span>
                    </div>
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 text-blue-500 rounded-lg border border-blue-500/20">
                       <Monitor className="w-4 h-4" /> <span className="text-[10px] font-bold">Bilibili</span>
                    </div>
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-stone-500/10 text-stone-300 rounded-lg border border-stone-500/20">
                       <Smartphone className="w-4 h-4" /> <span className="text-[10px] font-bold">Douyin</span>
                    </div>
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-stone-500/10 text-stone-300 rounded-lg border border-stone-500/20">
                       <CloudUpload className="w-4 h-4" /> <span className="text-[10px] font-bold">MP4 Support</span>
                    </div>
                 </div>

                 <div className="w-full max-w-xl space-y-6">
                    <div className="flex items-center justify-center gap-8">
                       <button 
                         onClick={() => setIsFastMode(true)}
                         className={`flex items-center gap-2 transition-all ${isFastMode ? "text-cyan-400" : "text-stone-500 hover:text-stone-300"}`}
                       >
                          <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${isFastMode ? "border-cyan-400" : "border-stone-700"}`}>
                             {isFastMode && <div className="w-2 h-2 bg-cyan-400 rounded-full" />}
                          </div>
                          <span className="text-xs font-bold">Tạo nhanh AI (15-60s)</span>
                       </button>
                       <button 
                         onClick={() => setIsFastMode(false)}
                         className={`flex items-center gap-2 transition-all ${!isFastMode ? "text-purple-400" : "text-stone-500 hover:text-stone-300"}`}
                       >
                          <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${!isFastMode ? "border-purple-400" : "border-stone-700"}`}>
                             {!isFastMode && <div className="w-2 h-2 bg-purple-400 rounded-full" />}
                          </div>
                          <span className="text-xs font-bold">Tùy chỉnh (Advanced)</span>
                       </button>
                    </div>

                    <Button 
                      className="group relative h-16 w-full max-w-xs rounded-2xl bg-gradient-to-r from-cyan-500 to-purple-600 p-[1.5px] hover:scale-105 transition-all"
                      onClick={handleStartAnalysis}
                    >
                       <div className="w-full h-full bg-black rounded-[14px] flex items-center justify-center gap-2 group-hover:bg-transparent transition-colors">
                          <Sparkles className="w-5 h-5 text-cyan-400 group-hover:text-white" />
                          <span className="text-lg font-black tracking-tighter text-white">PHÂN TÍCH BẰNG AI</span>
                          <ArrowRight className="w-4 h-4 text-white/50 group-hover:translate-x-1 transition-transform" />
                       </div>
                    </Button>
                 </div>
              </Card>
           </div>

           {/* Recent Projects Section OR AI Suggestions Gallery */}
           {isAnalyzing ? null : url && url.length > 10 ? (
              <div className="space-y-8 animate-in slide-in-from-bottom duration-1000">
                 <div className="flex items-center justify-between border-b border-white/5 pb-6">
                    <div className="space-y-1">
                       <h3 className="text-2xl font-black text-white tracking-tighter">AI SUGGESTIONS</h3>
                       <p className="text-stone-500 text-xs">Tìm thấy {generatedClips.length} đoạn clip có tiềm năng viral cao nhất</p>
                    </div>
                    <div className="flex items-center gap-3">
                       <Badge className="bg-cyan-500/10 text-cyan-400 border-cyan-400/20 px-3 py-1 text-[10px] font-bold">SCORE &gt; 85% 🔥</Badge>
                       <Button variant="outline" className="h-9 border-white/10 bg-white/5 text-xs font-bold gap-2">
                          <Plus className="w-3 h-3" /> Regenerate
                       </Button>
                       <Button className="h-9 bg-cyan-400 text-black hover:bg-cyan-300 text-xs font-black px-6">
                          EXPORT ALL ({generatedClips.length})
                       </Button>
                    </div>
                 </div>

                 <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {generatedClips.map((clip, i) => (
                       <Card key={i} className="bg-[#0a0a0a] border-white/5 overflow-hidden group cursor-pointer hover:border-cyan-400/50 transition-all rounded-3xl flex flex-col shadow-xl">
                          <div className="aspect-[9/16] bg-stone-900 relative overflow-hidden">
                             <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent z-10"></div>
                             
                             {/* Badge View */}
                             <div className="absolute top-4 left-4 z-20 flex flex-col gap-2">
                                <div className="bg-cyan-400 text-black text-[10px] font-black px-2 py-1 rounded-lg flex items-center gap-1 shadow-lg shadow-cyan-400/20">
                                   <Zap className="w-3 h-3 fill-black" /> {clip.virality_score || 90}
                                </div>
                             </div>

                             {/* Play Indicator */}
                             <div className="absolute inset-0 flex items-center justify-center z-20 opacity-0 group-hover:opacity-100 transition-opacity">
                                <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center border border-white/30">
                                   <Scissors className="w-6 h-6 text-white" />
                                </div>
                             </div>

                             {/* Duration */}
                             <div className="absolute bottom-4 right-4 z-20 bg-black/60 backdrop-blur-md px-2 py-1 rounded text-[10px] font-mono text-white flex items-center gap-1">
                                <Clock className="w-3 h-3" /> {clip.duration?.toFixed(1)}s
                             </div>
                             
                             <video 
                                src={`http://localhost:8000${clip.video_url || "/clips/" + clip.filename}`}
                                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-[3s]"
                                muted
                                onMouseOver={(e) => (e.target as HTMLVideoElement).play()}
                                onMouseOut={(e) => (e.target as HTMLVideoElement).pause()}
                             />
                          </div>

                          <div className="p-5 space-y-4 z-20">
                             <h4 className="text-sm font-bold text-white truncate">{clip.text || "Viral Clip #" + i}</h4>
                             
                             <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1">
                                   <div className="flex justify-between items-center text-[9px] font-bold text-stone-500">
                                      <span>HOOK</span>
                                      <span className="text-cyan-400">{clip.hook_score || 9.2}</span>
                                   </div>
                                   <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                                      <div className="h-full bg-cyan-400" style={{ width: `${(clip.hook_score || 9.2) * 10}%` }}></div>
                                   </div>
                                </div>
                                <div className="space-y-1">
                                   <div className="flex justify-between items-center text-[9px] font-bold text-stone-500">
                                      <span>RETENTION</span>
                                      <span className="text-purple-400">{clip.engagement_score || 8.8}</span>
                                   </div>
                                   <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                                      <div className="h-full bg-purple-400" style={{ width: `${(clip.engagement_score || 8.8) * 10}%` }}></div>
                                   </div>
                                </div>
                             </div>

                             <div className="flex items-center gap-2 pt-2">
                                <Button className="flex-1 h-9 bg-white/5 border border-white/10 hover:bg-white/10 text-[10px] font-bold rounded-xl" onClick={(e) => {
                                  e.stopPropagation();
                                  window.location.href = `/editor?task_id=${clip.task_id}&clip_id=${clip.id}`;
                                }}>
                                   Edit Clip
                                </Button>
                                <Button size="icon" className="h-9 w-9 bg-cyan-400/10 text-cyan-400 hover:bg-cyan-400 hover:text-black border border-cyan-400/20 rounded-xl">
                                   <CloudUpload className="w-4 h-4" />
                                </Button>
                             </div>
                          </div>
                       </Card>
                    ))}
                 </div>
              </div>
           ) : (
              <div className="space-y-6">
                 <div className="flex items-center justify-between">
                    <h3 className="text-xl font-bold text-white tracking-tight">Recent Projects</h3>
                    <Link href="/library" className="text-xs font-bold text-cyan-400 hover:underline flex items-center gap-1">
                       See all <ChevronRight className="w-3 h-3" />
                    </Link>
                 </div>

                 <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {[1, 2, 3, 4].map((i) => (
                       <Card key={i} className="bg-[#0a0a0a] border-white/5 group cursor-pointer hover:border-cyan-400/30 transition-all overflow-hidden rounded-2xl">
                          <div className="aspect-video bg-white/5 relative overflow-hidden">
                             <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/10 to-purple-500/10 group-hover:scale-110 transition-transform duration-500"></div>
                             <div className="absolute top-2 right-2">
                                <Badge className="bg-green-500/20 text-green-500 border-none text-[8px] px-1.5 h-4">COMPLETED</Badge>
                             </div>
                             <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40">
                                <Zap className="w-8 h-8 text-white fill-white animate-pulse" />
                             </div>
                          </div>
                          <div className="p-4 space-y-3">
                             <p className="text-xs font-bold text-white truncate group-hover:text-cyan-400 transition-colors">Project {i}: Video Viral 2026</p>
                             <div className="flex items-center justify-between">
                                <div className="flex items-center gap-1 text-stone-500">
                                   <Clock className="w-3 h-3" />
                                   <span className="text-[10px]">2 hours ago</span>
                                </div>
                                <span className="text-[10px] font-bold text-stone-400">12 clips</span>
                             </div>
                          </div>
                       </Card>
                    ))}
                 </div>
              </div>
           )}
        </div>
      </main>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
          height: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #1a1a1a;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #2a2a2a;
        }
      `}</style>
    </div>
  );
}
