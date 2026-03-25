import React from 'react';
import './Landing.css';

function Landing({ onStart }) {
  return (
    <div className="bg-surface text-on-surface selection:bg-primary-container selection:text-on-primary-container font-body">
      {/* Top Navigation Shell */}
      <nav className="bg-[#f7f9fb]/80 dark:bg-slate-950/80 backdrop-blur-xl docked full-width top-0 sticky z-50 shadow-sm shadow-slate-200/50 dark:shadow-none font-['Manrope'] antialiased tracking-tight">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center w-full">
          <div className="text-xl font-bold tracking-tighter text-slate-900 dark:text-slate-50">Paise Do Re (PDR)</div>
          <div className="hidden md:flex items-center space-gap-8 gap-x-8">
            <a className="text-slate-900 dark:text-white font-semibold border-b-2 border-slate-900 dark:border-slate-50 pb-1 hover:text-slate-900 dark:hover:text-white transition-all duration-300" href="#">Solutions</a>
            <a className="text-slate-500 dark:text-slate-400 font-medium hover:text-slate-900 dark:hover:text-white transition-all duration-300" href="#">Trust Pipeline</a>
            <a className="text-slate-500 dark:text-slate-400 font-medium hover:text-slate-900 dark:hover:text-white transition-all duration-300" href="#">Compliance</a>
            <a className="text-slate-500 dark:text-slate-400 font-medium hover:text-slate-900 dark:hover:text-white transition-all duration-300" href="#">Documentation</a>
          </div>
          <div className="flex items-center gap-4">
            <button className="text-[#565e74] dark:text-slate-300 font-medium hover:text-slate-900 dark:hover:text-white transition-all duration-300 active:scale-95">Login</button>
            <button onClick={onStart} className="gradient-primary text-on-primary px-6 py-2.5 rounded-lg font-semibold active:scale-95 transition-transform duration-200">Request Demo</button>
          </div>
        </div>
      </nav>
      <main>
        {/* Hero Section */}
        <section className="relative pt-24 pb-32 overflow-hidden">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">
            <div className="lg:col-span-7">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-surface-container-high text-on-surface-variant text-xs font-bold uppercase tracking-widest mb-8">
                <span className="w-2 h-2 rounded-full bg-tertiary"></span>
                Architectural Credit Intelligence
              </div>
              <h1 className="text-5xl lg:text-7xl font-headline font-extrabold text-[#0F172A] tracking-tighter leading-[1.1] mb-8">
                Credit decisions that <span className="text-primary italic">explain</span> themselves.
              </h1>
              <p className="text-xl text-on-surface-variant font-body leading-relaxed mb-12 max-w-2xl">
                PDR scores NTCs and MSMEs using behavioral signals from bank statements — no credit history required. Transition from binary approvals to nuanced risk intelligence.
              </p>
              <div className="flex flex-wrap gap-4">
                <button onClick={onStart} className="gradient-primary text-on-primary px-8 py-4 rounded-lg text-lg font-bold flex items-center gap-2 shadow-lg shadow-primary/20 active:scale-95 transition-transform">
                  View Demo Profiles
                  <span className="material-symbols-outlined">arrow_forward</span>
                </button>
                <a href="https://github.com/lubdhak123/pdr_2" target="_blank" rel="noopener noreferrer" className="bg-surface-container-high text-on-surface px-8 py-4 rounded-lg text-lg font-bold ghost-border active:scale-95 transition-transform text-center inline-block">
                  Documentation
                </a>
              </div>
            </div>
            <div className="lg:col-span-5 relative">
              <div className="relative z-10 rounded-lg overflow-hidden shadow-2xl shadow-slate-200/50">
                <img className="w-full h-auto" alt="Dashboard preview" src="https://lh3.googleusercontent.com/aida-public/AB6AXuA2oNjvphduYcZ9Xjv3g-izCeXAtup-mBqKcw1TXuH_DjaYlb4hWAIwIimyG6fVyQQpq9VC6-rWPP4FjbLS3Wxonz6WqeQ_vMt1kVn_EYlUAKmvSKvK6xhWHEc6D5YPGmO6wbk0KoU5sxEAwo1c-_FK2mYg1_Gv1eXM5aJVxSeHShgvRAjw0VXlsRYKHRDhcvFlB91IMwiuYb69T6uAzkT5LcpzpIPkyW-hyibTJZ3kbdhtvjaq9DhJXnpf3TolUboOdEfL621NAA" />
              </div>
              <div className="absolute -top-12 -right-12 w-64 h-64 bg-tertiary-fixed opacity-20 blur-[100px] rounded-full"></div>
              <div className="absolute -bottom-12 -left-12 w-64 h-64 bg-primary-container opacity-30 blur-[100px] rounded-full"></div>
            </div>
          </div>
        </section>
        
        {/* The 4-Layer Trust Pipeline */}
        <section className="py-24 bg-surface-container-low">
          <div className="max-w-7xl mx-auto px-6">
            <div className="mb-20">
              <h2 className="text-3xl font-headline font-bold text-[#0F172A] mb-4">The Trust Pipeline</h2>
              <p className="text-on-surface-variant font-body max-w-xl">A proprietary four-stage architectural framework designed to transform raw financial noise into high-fidelity credit signals.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-surface-container-lowest p-8 rounded-lg ghost-border hover:shadow-xl transition-shadow duration-500">
                <div className="w-12 h-12 rounded-full bg-surface-container-high flex items-center justify-center mb-6">
                  <span className="material-symbols-outlined text-primary">input</span>
                </div>
                <h3 className="font-headline font-bold text-xl mb-3">Ingest</h3>
                <p className="text-sm text-on-surface-variant leading-relaxed">Multi-source bank statement aggregation via OCR and API connectors with 99.8% field accuracy.</p>
              </div>
              <div className="bg-surface-container-lowest p-8 rounded-lg ghost-border hover:shadow-xl transition-shadow duration-500">
                <div className="w-12 h-12 rounded-full bg-surface-container-high flex items-center justify-center mb-6">
                  <span className="material-symbols-outlined text-primary">security_update_good</span>
                </div>
                <h3 className="font-headline font-bold text-xl mb-3">Forensics</h3>
                <p className="text-sm text-on-surface-variant leading-relaxed">Deep-level behavioral analysis detecting circulation, round-tripping, and synthetic balance inflation.</p>
              </div>
              <div className="bg-surface-container-lowest p-8 rounded-lg ghost-border hover:shadow-xl transition-shadow duration-500">
                <div className="w-12 h-12 rounded-full bg-surface-container-high flex items-center justify-center mb-6">
                  <span className="material-symbols-outlined text-primary">query_stats</span>
                </div>
                <h3 className="font-headline font-bold text-xl mb-3">XGBoost</h3>
                <p className="text-sm text-on-surface-variant leading-relaxed">Gradient boosting decision trees predicting probability of default based on 450+ non-traditional features.</p>
              </div>
              <div className="bg-surface-container-lowest p-8 rounded-lg ghost-border hover:shadow-xl transition-shadow duration-500 border-l-4 border-tertiary">
                <div className="w-12 h-12 rounded-full bg-tertiary-container flex items-center justify-center mb-6">
                  <span className="material-symbols-outlined text-tertiary" style={{ fontVariationSettings: "'FILL' 1" }}>verified_user</span>
                </div>
                <h3 className="font-headline font-bold text-xl mb-3">SHAP</h3>
                <p className="text-sm text-on-surface-variant leading-relaxed">The "Explainability Engine" - decomposing every score into local feature contributions for regulatory transparency.</p>
              </div>
            </div>
          </div>
        </section>
        
        {/* Alternative Scoring Features */}
        <section className="py-32">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl">
              <h2 className="text-4xl font-headline font-extrabold text-[#0F172A] mb-6 tracking-tight">Intelligence Beyond the Ledger</h2>
              <p className="text-lg text-on-surface-variant">Standard bureau reports miss 60% of the small business economy. Our features capture the "invisible" indicators of intent and resilience.</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

export default Landing;
