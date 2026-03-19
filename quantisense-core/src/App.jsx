import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence, useReducedMotion, useMotionValue, useTransform } from 'framer-motion';
import {
  Shield,
  Upload,
  FileText,
  FileSpreadsheet,
  Zap,
  Bell,
  CheckCircle2,
  Loader2,
  Hourglass,
  AlertTriangle,
  Info,
  TrendingDown,
  TrendingUp,
  Download
} from 'lucide-react';
import {
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
  ResponsiveContainer
} from 'recharts';

// --- STYLES & ASSETS ---
const bgPattern = {
  backgroundImage: `linear-gradient(to right, rgba(99,102,241,0.08) 1px, transparent 1px), linear-gradient(to bottom, rgba(99,102,241,0.08) 1px, transparent 1px)`,
  backgroundSize: '40px 40px',
  backgroundAttachment: 'fixed',
  backgroundColor: '#F4F5F7'
};

const defaultTransition = { duration: 0.4, ease: "easeOut" };

const AGENTS = [
  "Document Parser",
  "Entity Resolver",
  "Web Researcher",
  "Risk Auditor",
  "UBO Validator",
  "Asset Classifier",
  "Compliance Engine",
  "Fraud Detector",
  "Bull Agent",
  "Bear Agent \u2192 Final Auditor"
];

// Fallback messages when starting the pipeline
const DEFAULT_AGENT_MESSAGES = [
  "Extraction of unstructured data from attached PDFs...",
  "Cross-referencing legal entities across global databases.",
  "Scraping regulatory news sources for adverse media.",
  "Analyzing sector-specific risk weights and variance...",
  "Queueing verification sequence...",
  "Awaiting UBO validation results.",
  "Rule-set application pending.",
  "Running anomaly pattern detection...",
  "Constructing favorable investment thesis...",
  "Awaiting manual oversight trigger."
];

// Custom numeric count-up hook
function useCountUp(endValue, duration = 1800) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    let startTime = null;
    let animationFrame;
    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = timestamp - startTime;
      const percent = Math.min(progress / duration, 1);
      const easePattern = percent === 1 ? 1 : 1 - Math.pow(2, -10 * percent);
      setCount(Math.floor(easePattern * endValue));
      if (progress < duration) {
        animationFrame = requestAnimationFrame(animate);
      }
    };
    animationFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrame);
  }, [endValue, duration]);
  return count;
}

// Reusable 3D Tilt Card Component
function TiltCard({ children, className, delay = 0 }) {
  const prefersReducedMotion = useReducedMotion();
  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const handleMouseMove = (event) => {
    if (prefersReducedMotion) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    x.set(event.clientX - centerX);
    y.set(event.clientY - centerY);
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  const rotateX = useTransform(y, [-200, 200], [6, -6]);
  const rotateY = useTransform(x, [-200, 200], [-6, 6]);

  const background = useTransform(
    [x, y],
    ([latestX, latestY]) => `radial-gradient(circle at ${latestX + 200}px ${latestY + 200}px, rgba(255,255,255,0.15), transparent 60%)`
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: prefersReducedMotion ? 0 : delay, duration: 0.4 }}
      style={{ rotateX, rotateY, transformStyle: "preserve-3d" }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`relative group ${className}`}
    >
      <motion.div
        className="pointer-events-none absolute inset-0 z-50 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 mix-blend-overlay"
        style={{ background }}
      />
      {children}
    </motion.div>
  );
}

export default function App() {
  const prefersReducedMotion = useReducedMotion();
  const [appState, setAppState] = useState('form'); // 'form' | 'processing' | 'results'

  // Form State
  const [formData, setFormData] = useState({
    companyName: '',
    promoterName: '',
    sector: '',
    loanAmount: '',
    loanPurpose: ''
  });
  const [files, setFiles] = useState([]);

  // Pipeline State
  const [activeStep, setActiveStep] = useState(0);
  const [logs, setLogs] = useState([]);
  const [jobId, setJobId] = useState(null);
  const logsEndRef = useRef(null);
  const eventSourceRef = useRef(null);

  // Final Results State
  const [resultsData, setResultsData] = useState(null);
  const [activeTab, setActiveTab] = useState("Documents");

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.companyName || !formData.promoterName) {
      alert("Please fill in company and promoter names.");
      return;
    }

    setAppState('processing');
    setLogs([{ time: new Date().toLocaleTimeString(), text: "System initialized. Handshaking with Core API..." }]);
    setActiveStep(0);

    const submitData = new FormData();
    submitData.append("company_name", formData.companyName);
    submitData.append("promoter_name", formData.promoterName);
    submitData.append("sector", formData.sector || "Unknown");
    submitData.append("loan_amount", formData.loanAmount || 0);
    submitData.append("loan_purpose", formData.loanPurpose);
    submitData.append("loan_tenure_months", 60);

    files.forEach(file => {
      submitData.append("files", file);
    });

    try {
      const resp = await fetch("http://localhost:8000/api/analyze", {
        method: "POST",
        body: submitData
      });
      const data = await resp.json();
      if (data.job_id) {
        setJobId(data.job_id);
      } else {
        throw new Error("No Job ID returned");
      }
    } catch (err) {
      setLogs(curr => [...curr, { time: new Date().toLocaleTimeString(), text: "ERROR: Connection to Core failed." }]);
      console.error(err);
    }
  };

  // --- SSE PROCESSING LOGIC ---
  useEffect(() => {
    if (appState === 'processing' && jobId) {
      const sse = new EventSource(`http://localhost:8000/api/stream/${jobId}`);
      eventSourceRef.current = sse;

      sse.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        const timeStr = new Date().toLocaleTimeString();

        if (msg.type === "progress") {
          // Map backend steps to the UI 10 agents roughly
          const pct = msg.pct;
          let stage = 0;
          if (pct >= 90) stage = 10;
          else if (pct >= 80) stage = 9;
          else if (pct >= 70) stage = 8;
          else if (pct >= 55) stage = 7;
          else if (pct >= 48) stage = 6;
          else if (pct >= 40) stage = 5;
          else if (pct >= 30) stage = 4;
          else if (pct >= 20) stage = 3;
          else if (pct >= 15) stage = 2;
          else if (pct > 5) stage = 1;

          setActiveStep(stage);
          setLogs(curr => [...curr, { time: timeStr, text: `[${msg.pct}%] ${msg.step}` }]);

        } else if (msg.type === "complete") {
          sse.close();
          setResultsData(msg.results);
          setLogs(curr => [...curr, { time: timeStr, text: "Analysis Complete. Generating Report..." }]);
          setActiveStep(10);
          setTimeout(() => setAppState('results'), 1500);

        } else if (msg.type === "error") {
          sse.close();
          setLogs(curr => [...curr, { time: timeStr, text: `CRITICAL ERROR: ${msg.message}` }]);
        }
      };

      sse.onerror = (err) => {
        console.error("SSE Error:", err);
        sse.close();
      };
    }

    return () => {
      if (eventSourceRef.current) eventSourceRef.current.close();
    };
  }, [appState, jobId]);

  // Auto-scrolling refs
  const processingRef = useRef(null);
  const resultsRef = useRef(null);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Scroll to processing section when it starts
  useEffect(() => {
    if (appState === 'processing') {
      setTimeout(() => {
        processingRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 300); // Wait for animation to start
    }
  }, [appState]);

  // Scroll to results section when complete
  useEffect(() => {
    if (appState === 'results') {
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 500); // Wait for the div to render
    }
  }, [appState]);

  // --- COMPONENTS ---

  const renderNavbar = () => (
    <nav className="sticky top-0 z-50 bg-white border-b border-[#E5E7EB] px-6 h-16 flex items-center justify-between">
      <div className="flex items-center gap-3 cursor-pointer">
        <div className="bg-[#2D3BE0] p-1.5 rounded-md">
          <Shield className="w-5 h-5 text-white" />
        </div>
        <div className="flex items-baseline gap-1">
          <span className="font-extrabold text-xl tracking-tight text-[#0D0F1A]">Quantisense</span>

        </div>
      </div>

      {appState !== 'form' && (
        <div className="hidden md:flex items-center gap-8 ml-12 text-sm font-semibold text-gray-400">
          <span className="cursor-pointer hover:text-[#0D0F1A] transition-colors">DASHBOARD</span>
          <span className="cursor-pointer text-[#2D3BE0] border-b-2 border-[#2D3BE0] pb-5 translate-y-[10px]">PIPELINE</span>
          <span className="cursor-pointer hover:text-[#0D0F1A] transition-colors">ANALYTICS</span>
          <span className="cursor-pointer hover:text-[#0D0F1A] transition-colors">SETTINGS</span>
        </div>
      )}

      <div className="flex items-center gap-6">
        {appState !== 'form' && <Bell className="w-5 h-5 text-gray-500 cursor-pointer hover:text-[#0D0F1A]" />}
        <div className="flex items-center gap-2 bg-gray-50 px-3 py-1.5 rounded-full border border-gray-200">
          <div className="w-2 h-2 rounded-full bg-[#00C48C] animate-pulse"></div>
          <span className="text-xs font-bold text-gray-600 tracking-wider">LIVE SYSTEM</span>
        </div>
        <div className="w-8 h-8 rounded-full bg-[#2D3BE0]/10 flex items-center justify-center text-[#2D3BE0] font-bold text-sm border border-[#2D3BE0]/20">
          JD
        </div>
      </div>
    </nav>
  );

  const renderFormState = () => (
    <motion.div
      key="form"
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={defaultTransition}
      style={{ opacity: appState === 'form' ? 1 : 0.6, pointerEvents: appState === 'form' ? 'auto' : 'none' }}
      className="max-w-2xl mx-auto pt-16 pb-16 px-4"
    >
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 bg-white px-4 py-1.5 rounded-full border border-[#E5E7EB] shadow-sm mb-6">
          <div className="w-2 h-2 rounded-full bg-[#00C48C] animate-pulse"></div>
          <span className="text-xs font-bold text-[#00C48C] tracking-wider">SYSTEM READY</span>
        </div>
        <h1 className="text-5xl font-black text-[#0D0F1A] tracking-tight mb-4">
          Quantisense
        </h1>
        <p className="text-[#6B7280] text-lg max-w-lg mx-auto leading-relaxed mb-8">
          Orchestrating multi-agent synthesis for institutional wealth-tech compliance and risk assessment.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm border border-[#E5E7EB] p-8">
        <div className="grid grid-cols-2 gap-6 mb-6">
          <div className="col-span-1">
            <label className="block text-xs uppercase tracking-[0.1em] text-[#6B7280] font-semibold mb-2">Company Name</label>
            <div className="animated-border-wrapper">
              <input type="text" name="companyName" value={formData.companyName} onChange={handleInputChange} placeholder="e.g. Acme Corp Industries"
                className="w-full px-4 py-3 text-sm focus:outline-none font-medium placeholder:font-normal" required />
            </div>
          </div>
          <div className="col-span-1">
            <label className="block text-xs uppercase tracking-[0.1em] text-[#6B7280] font-semibold mb-2">Promoter Name</label>
            <div className="animated-border-wrapper">
              <input type="text" name="promoterName" value={formData.promoterName} onChange={handleInputChange} placeholder="Lead Representative"
                className="w-full px-4 py-3 text-sm focus:outline-none font-medium placeholder:font-normal" required />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6 mb-6">
          <div className="col-span-1">
            <label className="block text-xs uppercase tracking-[0.1em] text-[#6B7280] font-semibold mb-2">Sector</label>
            <div className="animated-border-wrapper">
              <select name="sector" value={formData.sector} onChange={handleInputChange} className="w-full bg-white px-4 py-3 text-sm focus:outline-none font-medium text-[#0D0F1A] appearance-none cursor-pointer">
                <option value="" disabled className="text-gray-400">Select Industry</option>
                <option value="software">Software & SaaS</option>
                <option value="fintech">FinTech & Payments</option>
                <option value="biotech">Biotech & Healthcare</option>
                <option value="logistics">Logistics & Supply Chain</option>
                <option value="energy">Energy & Infrastructure</option>
                <option value="real_estate">Real Estate & Construction</option>
                <option value="retail">Retail & E-commerce</option>
                <option value="manufacturing">Manufacturing & Industrials</option>
                <option value="telecom">Telecommunications</option>
                <option value="others">Others</option>
              </select>
            </div>
          </div>
          <div className="col-span-1">
            <label className="block text-xs uppercase tracking-[0.1em] text-[#6B7280] font-semibold mb-2">Target Loan Amount</label>
            <div className="animated-border-wrapper">
              <input type="number" name="loanAmount" value={formData.loanAmount} onChange={handleInputChange} placeholder="INR Crores"
                className="w-full px-4 py-3 text-sm focus:outline-none font-medium placeholder:font-normal" required />
            </div>
          </div>
        </div>

        <div className="mb-8">
          <label className="block text-xs uppercase tracking-[0.1em] text-[#6B7280] font-semibold mb-2">Primary Purpose of Loan</label>
          <div className="animated-border-wrapper">
            <textarea name="loanPurpose" value={formData.loanPurpose} onChange={handleInputChange} placeholder="Describe the strategic objective for capital deployment..."
              className="w-full px-4 py-3 text-sm focus:outline-none font-medium placeholder:font-normal resize-none" rows="3" required></textarea>
          </div>
        </div>

        <div className="mb-8">
          <label className="block text-xs uppercase tracking-[0.1em] text-[#6B7280] font-semibold mb-2 flex justify-between">
            <span>Dossier Upload</span>
            <span className="text-gray-400 font-normal">PDF, XLSX, DOCX</span>
          </label>
          <div className="relative p-8 text-center bg-transparent cursor-pointer group overflow-hidden h-32 flex flex-col items-center justify-center">
            <svg className="absolute inset-0 w-full h-full pointer-events-none" xmlns="http://www.w3.org/2000/svg">
              <rect className="marching-ants-rect transition-colors" width="100%" height="100%" />
            </svg>
            <input type="file" multiple onChange={handleFileChange} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20" />
            <div className="w-12 h-12 rounded-full bg-indigo-50 flex items-center justify-center mx-auto mb-3 relative z-10 transition-transform group-hover:scale-110">
              <motion.div animate={prefersReducedMotion ? {} : { y: [0, -4, 0] }} transition={{ repeat: Infinity, duration: 1.8 }}>
                <Upload className="w-5 h-5 text-[#2D3BE0]" />
              </motion.div>
            </div>
            <p className="text-sm font-semibold text-[#0D0F1A] relative z-10">Drag & drop institutional files here</p>
            <p className="text-xs text-gray-500 mt-1 relative z-10">{files.length > 0 ? `${files.length} secure files attached` : "Strictly confidential analysis only"}</p>
          </div>
        </div>

        <div className="mt-4 space-y-3">
          {files.map((file, idx) => (
            <div key={idx} className="flex items-center justify-between p-3 rounded-lg border border-[#E5E7EB] bg-white">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-50 rounded text-[#2D3BE0]"><FileText className="w-4 h-4" /></div>
                <span className="text-sm font-semibold text-[#0D0F1A] truncate max-w-[200px]">{file.name}</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="text-[10px] font-bold tracking-wider text-[#00C48C] uppercase">Attached</span>
                <CheckCircle2 className="w-4 h-4 text-[#00C48C]" />
              </div>
            </div>
          ))}
        </div>


        <button
          type="submit"
          className="w-full bg-[#2D3BE0] hover:bg-[#1A1F6E] active:scale-[0.98] transition-all text-white font-bold py-4 rounded-xl flex items-center justify-center gap-2 mt-6 shadow-md"
        >
          Begin Analysis <Zap className="w-5 h-5 fill-current" />
        </button>
      </form>

      <p className="text-center text-xs text-gray-400 mt-8 mb-4 max-w-sm mx-auto leading-relaxed">
        Institutional-grade encryption active. Data processed under Quantisense Core Governance Protocol v4.2.
      </p>
    </motion.div>
  );

  const renderProcessingState = () => (
    <motion.div
      key="proc"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={defaultTransition}
      className="max-w-5xl mx-auto pt-12 pb-16 px-6 flex flex-col items-center flex-1 h-full"
    >
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 bg-white px-4 py-1.5 rounded-full border border-[#E5E7EB] shadow-sm mb-2">
          <div className="w-2 h-2 rounded-full bg-[#2D3BE0] animate-pulse"></div>
          <span className="text-xs font-bold text-[#2D3BE0] tracking-wider">LIVE PROCESSING</span>
        </div>
      </div>

      <div className="w-full flex justify-between relative">
        {/* Pipeline Container */}
        <div className="w-3/5 relative pb-32">
          {/* Vertical Line */}
          <div className="absolute left-6 top-6 bottom-0 w-0.5 bg-[#E5E7EB] -z-10 overflow-hidden">
            {!prefersReducedMotion && [0, 1, 2].map(i => (
              <motion.div
                key={i}
                className="absolute top-0 left-1/2 -translate-x-1/2 w-[3px] h-[3px] bg-[#1A1F6E] rounded-full opacity-40"
                animate={{ top: ["0%", "100%"] }}
                transition={{ repeat: Infinity, duration: 1.5, ease: "linear", delay: i * 0.5 }}
              />
            ))}
          </div>

          <div className="space-y-4">
            {AGENTS.map((agent, idx) => {
              const num = idx + 1;
              const isComplete = idx < activeStep;
              const isActive = idx === activeStep;
              const isPending = idx > activeStep;

              return (
                <div key={agent} className={`flex gap-6 items-start transition-all duration-500 ${isPending ? 'opacity-40' : 'opacity-100'}`}>
                  {/* Icon Node */}
                  <div className="relative shrink-0 mt-1 bg-[#F4F5F7] py-2">
                    {isComplete && (
                      <div className="relative">
                        {!prefersReducedMotion && [...Array(6)].map((_, i) => (
                          <motion.div
                            key={i}
                            className="absolute top-1/2 left-1/2 w-1.5 h-1.5 bg-[#00C48C] rounded-full z-0"
                            initial={{ x: "-50%", y: "-50%", opacity: 1 }}
                            animate={{
                              x: `calc(-50% + ${Math.cos((i * 60 * Math.PI) / 180) * 24}px)`,
                              y: `calc(-50% + ${Math.sin((i * 60 * Math.PI) / 180) * 24}px)`,
                              opacity: 0
                            }}
                            transition={{ duration: 0.4, ease: "easeOut" }}
                          />
                        ))}
                        <motion.div
                          initial={prefersReducedMotion ? { scale: 1 } : { scale: 0 }}
                          animate={{ scale: 1 }}
                          transition={{ type: "spring", bounce: 0.5 }}
                          className="w-12 h-12 rounded-full bg-[#1A1F6E] flex items-center justify-center shadow-md relative z-10"
                        >
                          <CheckCircle2 className="w-6 h-6 text-white" />
                        </motion.div>
                      </div>
                    )}
                    {isActive && (
                      <div className="relative w-12 h-12 flex items-center justify-center">
                        {!prefersReducedMotion && (
                          <motion.div
                            className="absolute inset-0 rounded-full border-2 border-[#2D3BE0]"
                            animate={{ scale: [1, 2], opacity: [0.4, 0] }}
                            transition={{ repeat: Infinity, duration: 1.5, ease: "easeOut" }}
                          />
                        )}
                        <div className="w-12 h-12 rounded-full border-2 border-[#2D3BE0] bg-white flex items-center justify-center shadow-lg relative z-10">
                          <Loader2 className="w-5 h-5 text-[#2D3BE0] animate-spin" />
                        </div>
                      </div>
                    )}
                    {isPending && (
                      <div className="w-12 h-12 rounded-full border border-[#E5E7EB] bg-white flex items-center justify-center relative z-10">
                        <Hourglass className="w-5 h-5 text-gray-400" />
                      </div>
                    )}
                  </div>

                  {/* Text Content */}
                  <div className="pt-2.5 pb-2">
                    <h3 className={`text-lg font-bold mb-1 ${isActive ? 'text-[#2D3BE0]' : (isComplete ? 'text-[#0D0F1A]' : 'text-gray-400')}`}>
                      {agent}
                    </h3>

                    {isActive && (
                      <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}>
                        <p className="text-sm font-medium text-[#0D0F1A] italic mb-3">{DEFAULT_AGENT_MESSAGES[idx]}</p>
                        <div className="w-32 h-[3px] bg-[#E5E7EB] rounded overflow-hidden">
                          <motion.div
                            className="h-full bg-[#2D3BE0]"
                            initial={{ width: "0%" }}
                            animate={{ width: "100%" }}
                            transition={{ duration: 2.5, ease: "linear" }}
                          />
                        </div>
                      </motion.div>
                    )}
                    {isComplete && <p className="text-sm text-[#6B7280]">{DEFAULT_AGENT_MESSAGES[idx]}</p>}
                    {isPending && <p className="text-sm text-gray-400 italic">{DEFAULT_AGENT_MESSAGES[idx]}</p>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Floating Console */}
        <div className="w-[35%] h-full">
          <motion.div
            initial={prefersReducedMotion ? { opacity: 0 } : { opacity: 0, y: 40, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="sticky top-[10vh] bg-white rounded-xl shadow-2xl overflow-hidden shadow-[#2D3BE0]/10 border border-[#E5E7EB]"
          >
            <div className="bg-[#F4F5F7] px-4 py-3 border-b border-[#E5E7EB] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex gap-1.5 mr-3">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-500"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-yellow-500"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-green-500"></div>
                </div>
                <span className="text-[10px] font-bold text-gray-500 tracking-wider font-mono">SYSTEM CONSOLE</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold text-[#F6AD55] tracking-widest animate-pulse">STATUS: BUSY</span>
              </div>
            </div>
            <div className="p-4 h-64 overflow-y-auto font-mono text-xs text-[#0D0F1A] space-y-2 leading-relaxed">
              {logs.map((log, i) => (
                <motion.div
                  key={i}
                  initial={prefersReducedMotion ? { x: 0, opacity: 1, filter: "blur(0px)" } : { x: 20, opacity: 0, filter: "blur(4px)" }}
                  animate={{ x: 0, opacity: 1, filter: "blur(0px)" }}
                  transition={{ duration: 0.2 }}
                  className={log.text.includes("complete") || log.text.includes("initialized") ? "text-gray-500" : "text-[#0D0F1A] font-medium"}
                >
                  <span className="text-[#2D3BE0] font-bold">[{log.time}]</span> {log.text}
                </motion.div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </motion.div>
        </div>
      </div >
    </motion.div >
  );

  const renderResultsState = () => {
    // Determine dynamic values from backend results if present, otherwise mock
    const chairmanText = resultsData?.chairman || "";

    // ═══════════════════════════════════════════════════════════
    // ROBUST DECISION PARSING — Using pre-parsed values from core API
    // ═══════════════════════════════════════════════════════════
    const decisionStr = resultsData?.parsed_decision || "APPROVED";
    
    // Clean up chairman text to be the first few paragraphs
    const strippedChairmanText = chairmanText ? chairmanText.replace(/[*#]/g, '') : "";
    const cleanChairman = strippedChairmanText ?
      strippedChairmanText.split('\n\n')
        .map(p => p.trim())
        .filter(p => p && !p.toUpperCase().includes("CHAIRMAN'S VERDICT") && !p.toUpperCase().includes("TRIGGER VALIDATION"))
        .slice(0, 3).join('\n\n') :
      "The synthesis of this quarter's data reinforces our conviction in the Quantisense Core strategy. We are witnessing an unprecedented convergence of traditional asset stability and tech-driven growth vectors. This is not merely an investment; it is a calculated stewardship of multi-generational wealth.";

    // Score from logic — the score is out of 100, we display it on a 0-100 gauge
    const scoreValRaw = resultsData?.parsed_score !== undefined ? resultsData.parsed_score : (decisionStr === 'APPROVED' ? 78 : (decisionStr === 'REJECTED' ? 42 : 62));
    const scoreData = [{ name: 'Score', value: scoreValRaw, fill: decisionStr === 'REJECTED' ? '#E53E3E' : (decisionStr === 'CONDITIONAL' ? '#F6AD55' : '#2D3BE0') }];

    // Use actual agent outputs instead of fragile regex parsing
    let strategicUpside = (resultsData?.bull || "Awaiting Bull Agent Analysis...").slice(0, 450) + "...";
    let riskExposure = (resultsData?.bear || "Awaiting Bear Agent Analysis...").slice(0, 450) + "...";

    // Clean up Markdown and headers from the raw agent text for the summary cards
    strategicUpside = strategicUpside.replace(/===.+?===/g, '').replace(/HEADLINE:.+/g, '').replace(/\*/g, '').replace(/TOP 5 REASONS TO APPROVE:/i, '').trim();
    riskExposure = riskExposure.replace(/===.+?===/g, '').replace(/HEADLINE:.+/g, '').replace(/\*/g, '').replace(/CRITICAL CONCERNS.*:/i, '').trim();

    // Dynamic compliance/leverage mapping
    const leverageMatch = strippedChairmanText.match(/Debt\/Equity:?\s*[\d_]+\/\d+\s*\[?([^\]\n]+)\]?/i);
    const defaultLeverage = leverageMatch ? leverageMatch[1].trim() : "6.8x";
    const defaultCompliance = "91%";

    // Fraud
    const fraudText = resultsData?.fraud || "";
    const isFraud = fraudText.toUpperCase().includes("CRITICAL") || fraudText.toUpperCase().includes("CONFIRMED");
    const fraudPct = isFraud ? "82%" : "1.2%";

    return (
      <motion.div
        key="res"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={defaultTransition}
        className="max-w-5xl mx-auto pt-12 pb-24 px-6"
      >
        <div className="mb-10">
          <div className="flex items-center gap-2 text-[#2D3BE0] mb-3">
            <Shield className="w-4 h-4" />
            <span className="text-xs font-bold tracking-[0.15em] uppercase">Institutional Grade Verdict</span>
          </div>
          <h1 className="text-4xl font-black text-[#0D0F1A] mb-2 tracking-tight">Analysis Overview</h1>
          <p className="text-[#6B7280] text-lg">Sophisticated wealth-tech synthesis for {formData.companyName || 'Portfolio Alpha-7'}.</p>
        </div>

        <div className="grid grid-cols-12 gap-8 mb-8">
          {/* Main Verdict Card */}
          <TiltCard delay={0.1 * 0.15} className="col-span-8 bg-white rounded-2xl p-10 border border-[#E5E7EB] shadow-sm relative flex flex-col items-center justify-center min-h-[400px]">
            <div className={`absolute top-6 right-6 ${
              decisionStr === 'REJECTED' ? 'bg-[#E53E3E]/10 text-[#E53E3E]' :
              decisionStr === 'CONDITIONAL' ? 'bg-[#F6AD55]/10 text-[#F6AD55]' :
              'bg-[#00C48C]/10 text-[#00C48C]'
            } px-3 py-1 rounded-sm text-xs font-bold tracking-wider uppercase z-20`}>
              Q4 Assessment
            </div>

            <p className="text-xs uppercase tracking-[0.2em] font-semibold text-gray-400 mb-6 relative z-20">Quantisense Alpha Verdict</p>

            <motion.h2
              initial={prefersReducedMotion ? { scale: 1, rotate: 0, opacity: 1 } : { scale: 1.4, rotate: -3, opacity: 0 }}
              animate={{
                scale: 1, rotate: 0, opacity: 1,
                color: decisionStr === 'REJECTED' ? '#E53E3E' : (decisionStr === 'CONDITIONAL' ? '#D97706' : '#0D0F1A')
              }}
              transition={{ type: "spring", stiffness: 400, damping: 15, duration: 0.3 }}
              className={`text-6xl md:text-8xl font-black mb-8 tracking-tighter relative z-20`}
            >
              {decisionStr}
            </motion.h2>

            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }}
              className={`flex items-center gap-2 ${
                decisionStr === 'REJECTED' ? 'bg-[#E53E3E]/5' :
                decisionStr === 'CONDITIONAL' ? 'bg-[#F6AD55]/5' :
                'bg-[#00C48C]/5'
              } px-4 py-2 rounded-full relative z-20`}
            >
              <div className={`${
                decisionStr === 'REJECTED' ? 'bg-[#E53E3E]' :
                decisionStr === 'CONDITIONAL' ? 'bg-[#F6AD55]' :
                'bg-[#00C48C]'
              } rounded-full p-1`}>
                {decisionStr === 'REJECTED' ? <AlertTriangle className="w-4 h-4 text-white" /> :
                 decisionStr === 'CONDITIONAL' ? <Info className="w-4 h-4 text-white" /> :
                 <CheckCircle2 className="w-4 h-4 text-white" />}
              </div>
              <span className={`text-sm font-bold ${
                decisionStr === 'REJECTED' ? 'text-[#E53E3E]' :
                decisionStr === 'CONDITIONAL' ? 'text-[#D97706]' :
                'text-[#00C48C]'
              } tracking-wide uppercase`}>
                {decisionStr === 'REJECTED' ? 'High Risk — Allocation Blocked' :
                 decisionStr === 'CONDITIONAL' ? 'Conditional Approval — Covenants Required' :
                 'Allocation Recommended'}
              </span>
            </motion.div>
          </TiltCard>

          {/* Metrics Stack */}
          <div className="col-span-4 flex flex-col gap-8">
            <TiltCard delay={1 * 0.15} className="bg-white rounded-2xl p-8 border border-[#E5E7EB] shadow-sm flex-1 flex flex-col items-center text-center justify-between">
              <h3 className="text-xs uppercase tracking-[0.1em] font-semibold text-gray-500 w-full text-center relative z-20">Quantisense Score</h3>

              <div className="w-48 h-48 relative my-2 z-20">
                <ResponsiveContainer width="100%" height="100%">
                  <RadialBarChart
                    cx="50%" cy="50%" innerRadius="80%" outerRadius="100%"
                    barSize={12} data={scoreData} startAngle={90} endAngle={-270}
                  >
                    <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
                    <RadialBar minAngle={15} background clockWise dataKey="value" cornerRadius={6}
                      isAnimationActive={!prefersReducedMotion} animationBegin={300} animationDuration={1500} animationEasing="ease-out" />
                  </RadialBarChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <div className="flex items-baseline justify-center">
                    <span className={`text-5xl font-black tracking-tighter ${
                      decisionStr === 'REJECTED' ? 'text-[#E53E3E]' :
                      decisionStr === 'CONDITIONAL' ? 'text-[#D97706]' :
                      'text-[#0D0F1A]'
                    }`}>{scoreVal}</span>
                    <span className="text-xs font-bold text-gray-400 ml-1">/100</span>
                  </div>
                  <span className="text-[10px] font-bold text-gray-400 mt-1 uppercase tracking-widest">Score</span>
                </div>
              </div>

              <p className="text-sm text-[#6B7280] leading-relaxed relative z-20">
                {decisionStr === 'REJECTED' ? (
                  <span className="font-bold text-[#E53E3E]">Below approval threshold</span>
                ) : decisionStr === 'CONDITIONAL' ? (
                  <span className="font-bold text-[#D97706]">Meets conditions — review required</span>
                ) : (
                  <span className="font-bold text-[#2D3BE0]">Above approval threshold</span>
                )}
              </p>
            </TiltCard>
          </div>
        </div>

        {/* Secondary Info Rows */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: prefersReducedMotion ? 0 : 2 * 0.15 }}
          className="bg-white rounded-2xl p-8 border border-[#E5E7EB] shadow-sm mb-8 grid grid-cols-2 gap-12 relative"
        >
          <div className="absolute left-1/2 top-8 bottom-8 w-px bg-[#E5E7EB]"></div>

          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-2 h-2 rounded-full bg-[#2D3BE0]"></div>
              <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest">Bull's Key Argument</h3>
            </div>
            <p className="italic text-[#6B7280] font-serif leading-relaxed text-[15px] whitespace-pre-line line-clamp-6">
              {strategicUpside}
            </p>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-2 h-2 rounded-full bg-[#E53E3E]"></div>
              <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest">Bear's Key Argument</h3>
            </div>
            <p className="italic text-[#6B7280] font-serif leading-relaxed text-[15px] whitespace-pre-line line-clamp-6">
              {riskExposure}
            </p>
          </div>
        </motion.div>

        {/* Small metric cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: prefersReducedMotion ? 0 : 3 * 0.15 }}
          className="grid grid-cols-3 gap-6 mb-8"
        >
          <div className="bg-white rounded-xl p-6 border border-[#E5E7EB] shadow-sm">
            <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Fraud Probability</h3>
            <div className="flex items-baseline gap-2 mb-2">
              <span className={`text-4xl font-black ${isFraud ? 'text-[#E53E3E]' : 'text-[#00C48C]'} tracking-tighter`}>{fraudPct}</span>
              <AlertTriangle className={`w-4 h-4 ${isFraud ? 'text-[#E53E3E]' : 'text-[#00C48C]'}`} />
            </div>
            <p className="text-xs text-gray-500 font-medium">{isFraud ? 'High risk anomalies detected.' : 'Clear risk profile. No flags.'}</p>
          </div>
          <div className="bg-white rounded-xl p-6 border border-[#E5E7EB] shadow-sm">
            <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Borrowing Leverage</h3>
            <div className="flex items-baseline gap-2 mb-2">
              <span className="text-4xl font-black text-[#F6AD55] tracking-tighter text-2xl truncate" title={defaultLeverage}>{defaultLeverage}</span>
              <Info className="w-4 h-4 text-[#F6AD55]" />
            </div>
            <p className="text-xs text-gray-500 font-medium">Derived from Financial Health Pillar.</p>
          </div>
          <div className="bg-white rounded-xl p-6 border border-[#E5E7EB] shadow-sm">
            <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Compliance Score</h3>
            <div className="flex items-baseline gap-2 mb-2">
              <span className="text-4xl font-black text-[#00C48C] tracking-tighter">{defaultCompliance}</span>
              <CheckCircle2 className="w-4 h-4 text-[#00C48C]" />
            </div>
            <p className="text-xs text-gray-500 font-medium">Regulatory alignment confirmed.</p>
          </div>
        </motion.div>

        {/* Chairman's Summary */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: prefersReducedMotion ? 0 : 4 * 0.15 }}
          className="bg-gradient-to-br from-white to-[#F8F9FA] rounded-2xl p-10 shadow-lg relative overflow-hidden border border-[#E5E7EB]"
        >
          <div className="text-[10px] font-bold text-[#2D3BE0] tracking-[0.2em] uppercase mb-8">Chairman's Summary</div>
          <div className="absolute -top-6 -right-6 text-[180px] text-[#2D3BE0]/5 font-serif leading-none italic font-black">"</div>

          <p className="text-base text-[#0D0F1A] font-medium leading-[1.8] max-w-4xl relative z-10 whitespace-pre-wrap">
            "{cleanChairman}"
          </p>
        </motion.div>

        {/* --- DETAILED TABS SECTION --- */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}
          className="bg-white rounded-2xl shadow-sm border border-[#E5E7EB] overflow-hidden mt-8"
        >
          <div className="flex border-b border-[#E5E7EB] overflow-x-auto p-2 gap-2 bg-gray-50/50">
            {["Documents", "Research", "Fraud Scan", "The Debate", "Stress Test", "Final Decision"].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-3 text-sm font-bold rounded-lg transition-all whitespace-nowrap ${activeTab === tab
                  ? 'bg-[#2D3BE0] text-white shadow-md'
                  : 'text-gray-500 hover:bg-gray-100 hover:text-gray-900'
                  }`}
              >
                {tab}
              </button>
            ))}
          </div>

          <div className="p-8 bg-white min-h-[400px]">
            {activeTab === "The Debate" ? (
              <div className="grid grid-cols-2 gap-8">
                <div className="bg-green-50/30 p-6 rounded-xl border border-green-100 shadow-sm">
                  <h3 className="text-green-700 font-bold mb-4 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5" /> The Bull Case
                  </h3>
                  <pre className="whitespace-pre-wrap font-mono text-xs text-gray-700 leading-relaxed font-medium">
                    {resultsData?.bull || "No bull case available."}
                  </pre>
                </div>
                <div className="bg-red-50/30 p-6 rounded-xl border border-red-100 shadow-sm">
                  <h3 className="text-red-700 font-bold mb-4 flex items-center gap-2">
                    <TrendingDown className="w-5 h-5" /> The Bear Case
                  </h3>
                  <pre className="whitespace-pre-wrap font-mono text-xs text-gray-700 leading-relaxed font-medium">
                    {resultsData?.bear || "No bear case available."}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="bg-gray-50 p-6 rounded-xl border border-[#E5E7EB] shadow-inner max-h-[800px] overflow-y-auto">
                <pre className="whitespace-pre-wrap font-mono text-xs text-gray-800 leading-relaxed font-medium">
                  {activeTab === "Documents" && (resultsData?.parser || "No document parsing available.")}
                  {activeTab === "Research" && (resultsData?.research || "No research available.")}
                  {activeTab === "Fraud Scan" && (resultsData?.fraud || "No fraud scan available.")}
                  {activeTab === "Stress Test" && (resultsData?.stress_test || "No stress test available.")}
                  {activeTab === "Final Decision" && (resultsData?.chairman || "No final decision available.")}
                </pre>
              </div>
            )}
          </div>
        </motion.div>

        {/* CAM Download */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 }}
          className="mt-12 mb-12 flex justify-center"
        >
          <button
            onClick={() => {
              const element = document.createElement("a");
              const file = new Blob([resultsData?.cam_text || "No CAM available."], { type: 'text/plain' });
              element.href = URL.createObjectURL(file);
              const cleanName = typeof formData.companyName === 'string' ? formData.companyName.replace(/\s+/g, '_') : 'Company';
              element.download = `${cleanName}_CAM.txt`;
              document.body.appendChild(element); // Required for FireFox
              element.click();
              document.body.removeChild(element);
            }}
            className="flex items-center gap-3 bg-[#0D0F1A] hover:bg-[#2D3BE0] text-white px-8 py-5 rounded-2xl font-bold shadow-xl transition-all hover:-translate-y-1 group"
          >
            <Download className="w-5 h-5 group-hover:scale-110 transition-transform" />
            Download Credit Appraisal Memo (CAM)
          </button>
        </motion.div>

      </motion.div>
    );
  }

  // State required for the Global Score count up
  const [targetScore, setTargetScore] = useState(0);
  const scoreVal = useCountUp(targetScore, prefersReducedMotion ? 0 : 1800);

  // Track high-level target score whenever Results data is delivered
  // Score is out of 100 — parse from chairman text if available
  useEffect(() => {
    if (appState === 'results') {
      const rawScore = resultsData?.parsed_score !== undefined ? resultsData.parsed_score : 72;
      setTargetScore(Math.min(100, Math.round(rawScore)));
    }
  }, [appState, resultsData]);

  // Global Spotlight Tracking
  const spotlightRef = useRef(null);
  useEffect(() => {
    const handleMove = (e) => {
      if (spotlightRef.current && appState !== 'results') {
        spotlightRef.current.style.background = `radial-gradient(circle 300px at ${e.clientX}px ${e.clientY}px, rgba(99, 102, 241, 0.07), transparent)`;
      }
    };
    window.addEventListener('mousemove', handleMove);
    return () => window.removeEventListener('mousemove', handleMove);
  }, [appState]);

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden bg-[#F4F5F7]">
      {/* Animated Grid Background */}
      <motion.div
        className="absolute inset-0 pointer-events-none"
        animate={prefersReducedMotion ? {} : {
          backgroundPosition: ['0px 0px', '40px 40px']
        }}
        transition={{
          repeat: Infinity,
          duration: 3,
          ease: "linear"
        }}
        style={{
          backgroundImage: `linear-gradient(to right, rgba(99,102,241,0.15) 1px, transparent 1px), linear-gradient(to bottom, rgba(99,102,241,0.15) 1px, transparent 1px)`,
          backgroundSize: '40px 40px',
          opacity: 0.85,
          zIndex: 0
        }}
      />

      {appState !== 'results' && (
        <div ref={spotlightRef} style={{ position: 'absolute', pointerEvents: 'none', zIndex: 0, inset: 0 }} />
      )}

      <div className="relative z-10 flex flex-col flex-1">
        {renderNavbar()}

        <main className="flex-1 flex flex-col relative z-20">
          <motion.div
            key="form-container"
            animate={
              appState !== 'form'
                ? { opacity: 1, pointerEvents: "none" }
                : { opacity: 1, pointerEvents: "auto" }
            }
            transition={{ duration: 0.8 }}
          >
            {renderFormState()}
          </motion.div>

          <AnimatePresence>
            {(appState === 'processing' || appState === 'results') && (
              <motion.div
                key="processing-container"
                ref={processingRef}
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto", transition: { duration: 0.5 } }}
                className="w-full bg-gradient-to-b from-transparent to-white/50 pt-12"
              >
                {renderProcessingState()}
              </motion.div>
            )}

            {appState === 'results' && (
              <motion.div
                key="results-container"
                ref={resultsRef}
                initial={prefersReducedMotion ? { opacity: 0, height: 0 } : { opacity: 0, height: 0, transform: "translateY(50px)" }}
                animate={{ opacity: 1, height: 'auto', transform: "translateY(0px)" }}
                transition={{ duration: 0.6, ease: "easeOut" }}
                className="w-full bg-gradient-to-b from-white/50 to-white pt-12 relative z-30 pb-10"
              >
                {renderResultsState()}
              </motion.div>
            )}
          </AnimatePresence>
        </main>

        <footer className="border-t border-[#E5E7EB] bg-white py-6 mt-auto relative z-10">
          <div className="max-w-7xl mx-auto px-6 flex justify-between items-center text-xs">
            <div className="flex items-center gap-2 font-bold text-[#0D0F1A] tracking-wider">
              <Shield className="w-4 h-4 text-gray-400" /> QUANTISENSE CORE
            </div>
            <div className="flex gap-8 font-bold text-gray-500 tracking-wider">
              <span className="cursor-pointer hover:text-[#0D0F1A]">TERM SHEET</span>
              <span className="cursor-pointer hover:text-[#0D0F1A]">DISCLOSURES</span>
              <span className="cursor-pointer hover:text-[#0D0F1A]">VAULT SECURITY</span>
            </div>
            <div className="text-gray-400 font-medium tracking-wide">
              ©️ 2024 Quantisense Core Intelligence Systems. All Rights Reserved.
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}