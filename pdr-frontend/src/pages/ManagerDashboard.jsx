import { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, XCircle, Clock, Search, ArrowLeft, Users, MessageSquare, ChevronRight, FileText } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = 'http://localhost:8000';

export default function ManagerDashboard() {
  const [applicants, setApplicants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('NTC'); // NTC or MSME
  
  const [selectedApplicant, setSelectedApplicant] = useState(null);
  const [remarks, setRemarks] = useState('');
  const [showStatusModal, setShowStatusModal] = useState(false);
  
  const navigate = useNavigate();

  useEffect(() => {
    fetchApplicants();
  }, []);

  const fetchApplicants = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${BACKEND_URL}/api/manager/applicants`);
      setApplicants(res.data);
    } catch (err) {
      console.error("Failed to fetch applicants:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (actionType) => {
    if (!remarks.trim()) {
      alert("Please provide the officer remarks before approving or declining.");
      return;
    }
    try {
      await axios.put(`${BACKEND_URL}/api/manager/applicant/${selectedApplicant.applicant_id}/status`, {
        outcome: actionType === 'approve' ? 'APPROVED' : 'REJECTED',
        remarks: remarks
      });
      setShowStatusModal(true);
      setTimeout(() => {
        setShowStatusModal(false);
        setSelectedApplicant(null);
        setRemarks('');
        fetchApplicants();
      }, 1500);
    } catch (err) {
      console.error("Action failed:", err);
      alert("Failed to submit action");
    }
  };

  // Filter based on NTC or MSME
  const filtered = applicants.filter(a => {
    const isNTC = a.applicant_id.toLowerCase().startsWith('ntc');
    const isMSME = a.applicant_id.toLowerCase().startsWith('msme');
    
    // First apply tab filter
    if (activeTab === 'NTC' && !isNTC) return false;
    if (activeTab === 'MSME' && !isMSME) return false;

    // Then apply search filter
    return a.name?.toLowerCase().includes(searchTerm.toLowerCase()) || 
           a.applicant_id?.toLowerCase().includes(searchTerm.toLowerCase());
  });

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-white/10 bg-slate-900/50">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={() => navigate('/')} className="p-2 hover:bg-white/5 rounded-full transition-colors hidden md:block">
              <ArrowLeft size={24} />
            </button>
            <div>
              <h1 className="text-3xl font-headline font-bold">Loan Application Queue</h1>
              <p className="text-slate-400">Review, compare, and decision applications</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4 border border-white/10 rounded-lg bg-slate-950 p-1">
            <button 
              onClick={() => {setActiveTab('NTC'); setSelectedApplicant(null);}}
              className={`px-6 py-2 rounded-md font-semibold text-sm transition-all ${activeTab === 'NTC' ? 'bg-primary text-slate-950 shadow-lg' : 'text-slate-400 hover:text-white'}`}
            >
              NTC Borrowers
            </button>
            <button 
              onClick={() => {setActiveTab('MSME'); setSelectedApplicant(null);}}
              className={`px-6 py-2 rounded-md font-semibold text-sm transition-all ${activeTab === 'MSME' ? 'bg-primary text-slate-950 shadow-lg' : 'text-slate-400 hover:text-white'}`}
            >
              MSME Borrowers
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 flex max-w-7xl mx-auto w-full">
        {/* Left Side: Applicant List */}
        <div className={`w-full ${selectedApplicant ? 'lg:w-1/3 border-r border-white/10' : 'w-full'} flex flex-col`}>
          <div className="p-6 border-b border-white/5">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
              <input
                type="text"
                placeholder="Find applicant by ID or Name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-slate-900 border border-white/10 rounded-xl focus:ring-2 focus:ring-primary text-sm"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6 pt-0 space-y-4">
            {loading ? (
              <div className="flex justify-center py-20"><div className="w-8 h-8 rounded-full border-4 border-primary border-t-transparent animate-spin"/></div>
            ) : filtered.length === 0 ? (
              <div className="text-center py-10 text-slate-500">No {activeTab} applicants found.</div>
            ) : (
              filtered.map((app) => (
                <motion.div
                  key={app.applicant_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  onClick={() => setSelectedApplicant(app)}
                  className={`p-4 rounded-xl cursor-pointer border transition-all ${selectedApplicant?.applicant_id === app.applicant_id ? 'bg-slate-800 border-primary shadow-lg shadow-primary/20' : 'bg-slate-900 border-white/5 hover:border-white/20'}`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h3 className="font-bold text-lg">{app.name}</h3>
                      <p className="text-xs font-mono text-slate-400">{app.applicant_id}</p>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-xs font-bold font-mono ${app.default_probability < 0.2 ? 'text-green-400 bg-green-400/10' : app.default_probability < 0.5 ? 'text-amber-400 bg-amber-400/10' : 'text-rose-400 bg-rose-400/10'}`}>
                      {(app.default_probability * 100).toFixed(1)}% PD
                    </span>
                  </div>
                  <div className="flex justify-between items-center mt-4">
                    <span className="text-sm text-slate-400">Grade: <strong className="text-white">{app.grade}</strong></span>
                    <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-sm border ${
                      app.decision === 'APPROVED' ? 'border-green-500/30 text-green-400' :
                      app.decision === 'REJECTED' ? 'border-rose-500/30 text-rose-400' :
                      'border-amber-500/30 text-amber-500'
                    }`}>
                      {app.decision}
                    </span>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </div>

        {/* Right Side: Detailed Review Panel */}
        {selectedApplicant && (
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex-1 overflow-y-auto bg-slate-900/30 p-8"
          >
            <div className="flex justify-between items-start mb-8">
              <div>
                <span className="inline-block px-3 py-1 bg-white/5 text-slate-300 text-xs font-bold uppercase tracking-widest rounded-full mb-4">
                  Applicant Dossier
                </span>
                <h2 className="text-4xl font-headline font-extrabold text-white mb-2">{selectedApplicant.name}</h2>
                <div className="flex items-center gap-4 text-slate-400 text-sm">
                  <span className="font-mono">{selectedApplicant.applicant_id}</span>
                  <span>•</span>
                  <span>{selectedApplicant.city || 'Location Unknown'}</span>
                </div>
              </div>
              
              <div className="text-right">
                <p className="text-sm text-slate-400 mb-1">Model Recommended Status</p>
                <div className={`px-4 py-2 rounded-lg font-bold inline-block border ${
                      selectedApplicant.decision === 'APPROVED' ? 'border-green-500 bg-green-500/10 text-green-400' :
                      selectedApplicant.decision === 'REJECTED' ? 'border-rose-500 bg-rose-500/10 text-rose-400' :
                      'border-amber-500 bg-amber-500/10 text-amber-500'
                    }`}>
                  {selectedApplicant.decision}
                </div>
              </div>
            </div>

            {/* Application Data Grid */}
            <div className="grid grid-cols-2 gap-6 mb-8">
              <div className="p-6 bg-slate-950 rounded-2xl border border-white/5 shadow-inner">
                <p className="text-sm text-slate-400 mb-2 flex items-center gap-2"><FileText size={16}/> Credit Grade</p>
                <p className="text-5xl font-black font-mono">{selectedApplicant.grade}</p>
              </div>
              <div className="p-6 bg-slate-950 rounded-2xl border border-white/5 shadow-inner">
                <p className="text-sm text-slate-400 mb-2 flex items-center gap-2"><CheckCircle size={16}/> Prob. of Default</p>
                <p className={`text-4xl font-black ${selectedApplicant.default_probability < 0.2 ? 'text-green-400' : selectedApplicant.default_probability < 0.5 ? 'text-amber-400' : 'text-rose-400'}`}>
                  {(selectedApplicant.default_probability * 100).toFixed(2)}%
                </p>
              </div>
              <div className="col-span-2 p-6 bg-slate-950 rounded-2xl border border-white/5 shadow-inner">
                <p className="text-sm text-slate-400 mb-2 flex items-center gap-2"><MessageSquare size={16}/> AI Explainability Reason</p>
                <p className="text-lg font-medium leading-relaxed italic text-indigo-200">
                  {selectedApplicant.primary_reason || "No specific model reason provided."}
                </p>
              </div>
            </div>

            {/* Officer Action Area */}
            <div className="mt-12 bg-surface border border-white/10 p-8 rounded-3xl shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 blur-[80px] rounded-full"></div>
              
              <h3 className="text-xl font-bold mb-6 font-headline text-white">Manager Review</h3>
              
              <label className="block text-sm font-medium text-slate-400 mb-2">Officer Remarks (Visible to Applicant)</label>
              <textarea
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                className="w-full bg-slate-950 border border-white/10 rounded-xl p-4 text-white placeholder-slate-600 focus:ring-2 focus:ring-primary focus:outline-none min-h-[120px] mb-6 resize-none relative z-10"
                placeholder="Enter reasoning for your final decision here..."
              />

              <div className="flex gap-4 relative z-10">
                <button 
                  onClick={() => handleAction('approve')}
                  className="flex-1 py-4 bg-green-600 hover:bg-green-500 text-white font-bold rounded-xl shadow-[0_0_20px_rgba(22,163,74,0.2)] transition-all flex justify-center items-center gap-2 text-lg active:scale-95"
                >
                  <CheckCircle size={22} /> Approve Loan
                </button>
                <button 
                  onClick={() => handleAction('reject')}
                  className="flex-1 py-4 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-xl shadow-[0_0_20px_rgba(225,29,72,0.2)] transition-all flex justify-center items-center gap-2 text-lg active:scale-95"
                >
                  <XCircle size={22} /> Decline Loan
                </button>
              </div>
            </div>
          </motion.div>
        )}
        
        {!selectedApplicant && (
          <div className="hidden lg:flex flex-1 items-center justify-center flex-col text-slate-500 p-8 text-center bg-slate-900/10">
            <Users size={64} className="mb-6 opacity-20" />
            <h3 className="text-2xl font-bold text-slate-400 mb-2">Select an Applicant</h3>
            <p className="max-w-md">Click on an applicant from the {activeTab} queue on the left to review their detailed risk dossier and submit a final decision.</p>
          </div>
        )}
      </div>

      {/* Success Modal */}
      <AnimatePresence>
        {showStatusModal && (
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md"
          >
            <motion.div initial={{ scale: 0.9 }} animate={{ scale: 1 }} exit={{ scale: 0.9 }} className="bg-slate-900 p-8 rounded-3xl flex flex-col items-center border border-white/10 shadow-2xl">
              <div className="w-16 h-16 bg-primary/20 rounded-full flex items-center justify-center text-primary mb-4">
                <CheckCircle size={32} />
              </div>
              <h2 className="text-2xl font-bold">Decision Recorded!</h2>
              <p className="text-slate-400 mt-2">The applicant status has been updated securely.</p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
