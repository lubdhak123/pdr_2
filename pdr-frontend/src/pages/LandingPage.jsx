import React from 'react';
import { Link } from 'react-router-dom';

function LandingPage() {
  return (
    <div className="bg-surface text-on-surface selection:bg-primary-container selection:text-on-primary-container">
      {/* Top Navigation Shell */}
      <nav className="bg-[#f7f9fb]/80 dark:bg-slate-950/80 backdrop-blur-xl top-0 sticky z-50 shadow-sm shadow-slate-200/50 dark:shadow-none font-['Manrope'] antialiased tracking-tight">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center w-full">
          <div className="text-xl font-bold tracking-tighter text-slate-900 dark:text-slate-50">Paise Do Re (PDR)</div>
          <div className="hidden md:flex items-center gap-x-8">
            <a className="text-slate-500 dark:text-slate-400 font-medium hover:text-slate-900 dark:hover:text-white transition-all duration-300" href="#problem-statement">About Us</a>
            <a className="text-slate-900 dark:text-white font-semibold border-b-2 border-slate-900 dark:border-slate-50 pb-1 hover:text-slate-900 dark:hover:text-white transition-all duration-300" href="#trust-pipeline">Solutions</a>
            <a className="text-slate-500 dark:text-slate-400 font-medium hover:text-slate-900 dark:hover:text-white transition-all duration-300" href="#trust-pipeline">Trust Pipeline</a>
            <a className="text-slate-500 dark:text-slate-400 font-medium hover:text-slate-900 dark:hover:text-white transition-all duration-300" href="#intelligence">Compliance</a>
            <a className="text-slate-500 dark:text-slate-400 font-medium hover:text-slate-900 dark:hover:text-white transition-all duration-300" href="#intelligence">Documentation</a>
          </div>
          <div className="flex items-center gap-4">
            <button className="text-[#565e74] dark:text-slate-300 font-medium hover:text-slate-900 dark:hover:text-white transition-all duration-300 active:scale-95">Login</button>
            <Link to="/solutions" className="gradient-cta text-white px-6 py-2.5 rounded-lg font-semibold active:scale-95 transition-transform duration-200">Request Demo</Link>
          </div>
        </div>
      </nav>

      <main>
        {/* SECTION 1: HERO */}
        <section className="relative pt-24 pb-32 overflow-hidden bg-surface">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">
            <div className="lg:col-span-7">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-surface-container-high text-on-surface-variant text-xs font-bold uppercase tracking-widest mb-8">
                <span className="w-2 h-2 rounded-full bg-tertiary"></span>
                Architectural Credit Intelligence
              </div>
              <h1 className="text-5xl lg:text-7xl font-headline font-extrabold text-[#0F172A] tracking-tighter leading-[1.1] mb-8">
                Credit decisions that <span className="text-tertiary italic">explain</span> themselves.
              </h1>
              <p className="text-xl text-on-surface-variant font-body leading-relaxed mb-12 max-w-2xl">
                PDR scores NTCs and MSMEs using behavioral signals from bank statements — no credit history required.
              </p>
              <div className="flex flex-wrap gap-4">
                <Link to="/solutions" className="gradient-cta text-white px-8 py-4 rounded-lg text-lg font-bold flex items-center gap-2 shadow-lg shadow-tertiary/20 active:scale-95 transition-transform">
                  Score a Business Free →
                </Link>
                <Link to="/docs" className="bg-transparent text-on-surface px-8 py-4 rounded-lg text-lg font-bold ghost-border active:scale-95 transition-transform">
                  Documentation
                </Link>
              </div>
            </div>
            <div className="lg:col-span-5 relative">
              <div className="relative z-10 p-8 rounded-3xl bg-[#0F172A] shadow-2xl">
                {/* Clean White Card Mockup */}
                <div className="bg-white rounded-2xl p-8 shadow-inner">
                  <div className="flex justify-between items-start mb-10">
                    <div>
                      <span className="inline-flex items-center px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold border border-emerald-100 mb-3">
                        Grade A — Strong
                      </span>
                      <h4 className="text-3xl font-black text-slate-900">PD: 4.2%</h4>
                    </div>
                    <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center">
                      <span className="material-symbols-outlined text-emerald-600">verified</span>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2">SHAP Explainability Tags</p>
                    <div className="flex flex-wrap gap-2">
                      <span className="px-3 py-1.5 rounded-full bg-slate-50 text-slate-700 text-xs font-medium border border-slate-100 flex items-center gap-1.5">
                        <span className="text-emerald-500 font-bold">✓</span> Cashflow Stable
                      </span>
                      <span className="px-3 py-1.5 rounded-full bg-slate-50 text-slate-700 text-xs font-medium border border-slate-100 flex items-center gap-1.5">
                        <span className="text-emerald-500 font-bold">✓</span> GST Consistent
                      </span>
                      <span className="px-3 py-1.5 rounded-full bg-slate-50 text-slate-700 text-xs font-medium border border-slate-100 flex items-center gap-1.5">
                        <span className="text-amber-500 font-bold">⚠</span> High Concentration Risk
                      </span>
                    </div>
                  </div>
                  <div className="mt-8 pt-6 border-t border-slate-100">
                    <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-500 w-[92%]"></div>
                    </div>
                    <div className="flex justify-between mt-2 text-[10px] font-bold text-slate-400">
                      <span>CONFIDENCE SCORE</span>
                      <span>92%</span>
                    </div>
                  </div>
                </div>
              </div>
              <div className="absolute -top-12 -right-12 w-64 h-64 bg-tertiary-fixed opacity-20 blur-[100px] rounded-full"></div>
              <div className="absolute -bottom-12 -left-12 w-64 h-64 bg-primary-container opacity-30 blur-[100px] rounded-full"></div>
            </div>
          </div>
        </section>

        {/* SECTION 2: ₹28 TRILLION BLIND SPOT */}
        <section className="py-24 bg-surface border-t border-outline-variant/10" id="problem-statement">
          <div className="max-w-7xl mx-auto px-6 text-center">
            <div className="inline-block px-4 py-1.5 mb-6 rounded-full bg-tertiary-container text-on-tertiary-container text-xs font-bold tracking-widest uppercase font-label">
              The Systemic Crisis
            </div>
            <h2 className="text-5xl md:text-7xl font-extrabold text-slate-900 tracking-tighter mb-8 leading-[0.9] font-headline">
              The ₹28 Trillion <br /><span className="text-tertiary">Blind Spot.</span>
            </h2>
            <div className="max-w-2xl mx-auto mb-16">
              <p className="text-lg md:text-xl text-on-surface-variant leading-relaxed font-body">
                India's financial engine is firing on half its cylinders. A ₹28T gap separates capital from the businesses that need it.
              </p>
            </div>
            {/* Impact Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
              {/* Card 1 */}
              <div className="group p-8 rounded-lg bg-surface-container-lowest border border-outline-variant/15 hover:border-tertiary/40 transition-all duration-500 shadow-sm">
                <div className="flex flex-col h-full">
                  <span className="material-symbols-outlined text-tertiary text-4xl mb-6">groups</span>
                  <h3 className="text-4xl font-black text-slate-900 tracking-tight mb-2 font-headline">450 Million</h3>
                  <p className="text-on-surface-variant font-medium">Credit-Invisible Individuals</p>
                  <div className="mt-auto pt-8 border-t border-outline-variant/10">
                    <p className="text-sm text-on-surface-variant/80 italic">A population larger than the United States, ignored by legacy scoring.</p>
                  </div>
                </div>
              </div>
              {/* Card 2 */}
              <div className="group p-8 rounded-lg bg-surface-container-lowest border border-outline-variant/15 hover:border-tertiary/40 transition-all duration-500 shadow-sm">
                <div className="flex flex-col h-full">
                  <span className="material-symbols-outlined text-tertiary text-4xl mb-6">storefront</span>
                  <h3 className="text-4xl font-black text-slate-900 tracking-tight mb-2 font-headline">63 Million</h3>
                  <p className="text-on-surface-variant font-medium">Excluded MSMEs</p>
                  <div className="mt-auto pt-8 border-t border-outline-variant/10">
                    <p className="text-sm text-on-surface-variant/80 italic">Small businesses fueling 30% of GDP, yet starved of working capital.</p>
                  </div>
                </div>
              </div>
              {/* Card 3 */}
              <div className="group p-8 rounded-lg bg-tertiary text-on-tertiary transition-all duration-500 shadow-xl shadow-tertiary/10">
                <div className="flex flex-col h-full">
                  <span className="material-symbols-outlined text-white text-4xl mb-6">payments</span>
                  <h3 className="text-4xl font-black text-white tracking-tight mb-2 font-headline">₹28 Trillion</h3>
                  <p className="text-tertiary-container font-medium">Systemic Financing Gap</p>
                  <div className="mt-auto pt-8 border-t border-tertiary-fixed-dim/20">
                    <p className="text-sm text-tertiary-container/90 italic">The annual capital deficit choking the growth of Emerging India.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION 4: THE SAFE-BORROWER DEFAULT LOOP */}
        <section className="py-32 bg-surface">
          <div className="max-w-7xl mx-auto px-6">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-24 items-start">
              {/* Narrative Column */}
              <div className="lg:col-span-4 space-y-10">
                <h2 className="text-4xl font-bold tracking-tight text-slate-900 leading-tight font-headline">
                  The Safe-Borrower <br />Default Loop
                </h2>
                <div className="space-y-8 text-on-surface-variant leading-relaxed text-lg font-body">
                  <p>
                    Traditional banking institutions are locked in a structural paradox. Bound by rigid credit-score mandates, they prioritize <span className="text-slate-900 font-semibold underline decoration-tertiary/30 decoration-2">"Safe Borrowers"</span>—those who already have capital.
                  </p>
                  <p>
                    This "Trust Deficit" isn't a lack of reliability; it's a lack of data visibility. Banks are saying no to growth they cannot measure.
                  </p>
                  <p>
                    PDR breaks this cycle by surfacing behavioral reliability through deep forensic analysis of cashflows.
                  </p>
                </div>
              </div>
              {/* Visual Column (Bento-style Charts) */}
              <div className="lg:col-span-8 flex flex-col gap-8">
                {/* Gap Paradox */}
                <div className="w-full">
                  <h4 className="text-xl font-bold text-slate-900 mb-4 font-headline uppercase tracking-tight">Gap Paradox Analysis</h4>
                  <div className="bg-surface-container-lowest p-10 rounded-2xl shadow-sm border border-outline-variant/10">
                    <div className="space-y-10">
                      <div className="space-y-3">
                        <div className="flex justify-between text-sm font-bold">
                          <span>FORMAL SUPPLY</span>
                          <span>₹35T</span>
                        </div>
                        <div className="h-6 bg-surface-container-highest rounded-full overflow-hidden">
                          <div className="h-full bg-slate-400 w-full rounded-full"></div>
                        </div>
                      </div>
                      <div className="space-y-3">
                        <div className="flex justify-between text-sm font-bold text-tertiary">
                          <span>UNMET GAP</span>
                          <span>₹28T</span>
                        </div>
                        <div className="h-6 bg-tertiary-container rounded-full overflow-hidden">
                          <div className="h-full bg-tertiary w-[80%] rounded-full"></div>
                        </div>
                      </div>
                    </div>
                    <p className="mt-8 text-sm text-on-surface-variant font-body">The unmet gap now rivals 80% of the total formal supply volume.</p>
                  </div>
                </div>
                {/* Shrinking Gateway */}
                <div className="w-full">
                  <h4 className="text-xl font-bold text-slate-900 mb-4 font-headline uppercase tracking-tight">Shrinking Gateway</h4>
                  <div className="bg-[#0F172A] p-10 rounded-2xl shadow-xl">
                    <div className="relative h-48 flex items-end justify-between px-4 mb-8">
                      <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 100">
                        <path d="M0 20 L25 25 L50 40 L75 55 L100 65" fill="none" stroke="#82ff99" strokeLinecap="round" strokeWidth="4"></path>
                        <path d="M0 20 L25 25 L50 40 L75 55 L100 65 L100 100 L0 100 Z" fill="url(#grad-landing)" opacity="0.1"></path>
                        <defs>
                          <linearGradient id="grad-landing" x1="0%" x2="0%" y1="0%" y2="100%">
                            <stop offset="0%" stopColor="#82ff99" stopOpacity="1"></stop>
                            <stop offset="100%" stopColor="#82ff99" stopOpacity="0"></stop>
                          </linearGradient>
                        </defs>
                      </svg>
                      <div className="z-10 text-center">
                        <span className="block text-4xl font-black text-white">21%</span>
                        <span className="block text-xs text-slate-500 font-bold mt-2">DEC 23</span>
                      </div>
                      <div className="z-10 text-center">
                        <span className="block text-4xl font-black text-tertiary-fixed">17%</span>
                        <span className="block text-xs text-slate-500 font-bold mt-2">DEC 24</span>
                      </div>
                    </div>
                    <div className="pt-6 border-t border-slate-800">
                      <p className="text-sm text-slate-400 mb-1 font-body">NTC Inclusion Trend</p>
                      <h4 className="text-xl font-bold text-white tracking-tight font-headline">Access is tightening, not expanding.</h4>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION 5: TRUST PIPELINE */}
        <section className="py-32 bg-surface-container-low" id="trust-pipeline">
          <div className="max-w-7xl mx-auto px-6">
            <div className="mb-20">
              <h2 className="text-4xl font-headline font-bold text-[#0F172A] mb-6">The Trust Pipeline</h2>
              <p className="text-lg text-on-surface-variant font-body max-w-2xl">A proprietary four-stage architectural framework designed to transform raw financial noise into high-fidelity credit signals.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Step 1 */}
              <div className="bg-surface-container-lowest p-10 rounded-2xl border-l-[4px] border-[#3B82F6] hover:shadow-2xl transition-all duration-500 flex flex-col min-h-[320px]">
                <div className="w-14 h-14 rounded-full bg-[#3B82F6]/10 flex items-center justify-center mb-8">
                  <span className="material-symbols-outlined text-[#3B82F6]">database</span>
                </div>
                <h3 className="font-headline font-bold text-2xl mb-4">Ingest</h3>
                <p className="text-base text-on-surface-variant leading-relaxed">Multi-source bank statement aggregation via OCR and API connectors with 99.8% field accuracy.</p>
              </div>
              {/* Step 2 */}
              <div className="bg-surface-container-lowest p-10 rounded-2xl border-l-[4px] border-[#EF4444] hover:shadow-2xl transition-all duration-500 flex flex-col min-h-[320px]">
                <div className="w-14 h-14 rounded-full bg-[#EF4444]/10 flex items-center justify-center mb-8">
                  <span className="material-symbols-outlined text-[#EF4444]">shield</span>
                </div>
                <h3 className="font-headline font-bold text-2xl mb-4">Forensics</h3>
                <p className="text-base text-on-surface-variant leading-relaxed">Deep-level behavioral analysis detecting circulation, round-tripping, and synthetic balance inflation.</p>
              </div>
              {/* Step 3 */}
              <div className="bg-surface-container-lowest p-10 rounded-2xl border-l-[4px] border-[#8B5CF6] hover:shadow-2xl transition-all duration-500 flex flex-col min-h-[320px]">
                <div className="w-14 h-14 rounded-full bg-[#8B5CF6]/10 flex items-center justify-center mb-8">
                  <span className="material-symbols-outlined text-[#8B5CF6]">psychology</span>
                </div>
                <h3 className="font-headline font-bold text-2xl mb-4">XGBoost</h3>
                <p className="text-base text-on-surface-variant leading-relaxed">Gradient boosting decision trees predicting probability of default based on 450+ non-traditional features.</p>
              </div>
              {/* Step 4 */}
              <div className="bg-surface-container-lowest p-10 rounded-2xl border-l-[4px] border-[#22C55E] hover:shadow-2xl transition-all duration-500 flex flex-col min-h-[320px]">
                <div className="w-14 h-14 rounded-full bg-[#22C55E]/10 flex items-center justify-center mb-8">
                  <span className="material-symbols-outlined text-[#22C55E]">bar_chart</span>
                </div>
                <h3 className="font-headline font-bold text-2xl mb-4">SHAP</h3>
                <p className="text-base text-on-surface-variant leading-relaxed">The "Explainability Engine" - decomposing every score into local feature contributions for regulatory transparency.</p>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION 6: INTELLIGENCE BEYOND THE LEDGER */}
        <section className="py-32" id="intelligence">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex flex-col md:flex-row justify-between items-end gap-8 mb-20">
              <div className="max-w-2xl">
                <h2 className="text-4xl font-headline font-extrabold text-[#0F172A] mb-6 tracking-tight">Intelligence Beyond the Ledger</h2>
                <p className="text-lg text-on-surface-variant">Standard bureau reports miss 60% of the small business economy. Our features capture the "invisible" indicators of intent and resilience.</p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {/* Feature 1 */}
              <div className="group p-10 bg-surface-container-lowest rounded-lg border border-outline-variant/15 hover:bg-surface-bright transition-colors">
                <h4 className="text-xs font-bold uppercase tracking-[0.2em] text-tertiary mb-6">Grade A Strong</h4>
                <h3 className="text-2xl font-headline font-bold text-[#0F172A] mb-4">Psychometric Risk Analysis</h3>
                <p className="text-on-surface-variant leading-relaxed mb-8">Proprietary logic that maps repayment behavior against seasonal volatility to determine borrower "character" under stress.</p>
                <div className="h-1 w-full bg-surface-container rounded-full overflow-hidden">
                  <div className="h-full bg-tertiary w-4/5"></div>
                </div>
              </div>
              {/* Feature 2 */}
              <div className="group p-10 bg-surface-container-lowest rounded-lg border border-outline-variant/15 hover:bg-surface-bright transition-colors">
                <h4 className="text-xs font-bold uppercase tracking-[0.2em] text-amber-600 mb-6">Grade C Watch</h4>
                <h3 className="text-2xl font-headline font-bold text-[#0F172A] mb-4">Cashflow Integrity</h3>
                <p className="text-on-surface-variant leading-relaxed mb-8">Isolation of true revenue from loan churn, intra-day reversals, and suspicious inward remittances.</p>
                <div className="h-1 w-full bg-surface-container rounded-full overflow-hidden">
                  <div className="h-full bg-amber-500 w-1/2"></div>
                </div>
              </div>
              {/* Feature 3 */}
              <div className="group p-10 bg-surface-container-lowest rounded-lg border border-outline-variant/15 hover:bg-surface-bright transition-colors">
                <h4 className="text-xs font-bold uppercase tracking-[0.2em] text-error mb-6">Grade E Risk</h4>
                <h3 className="text-2xl font-headline font-bold text-[#0F172A] mb-4">Fraud Loop Detection</h3>
                <p className="text-on-surface-variant leading-relaxed mb-8">AI-driven mapping of connected party transactions to detect hidden leverage across multiple legal entities.</p>
                <div className="h-1 w-full bg-surface-container rounded-full overflow-hidden">
                  <div className="h-full bg-error w-1/4"></div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* FOOTER / BOTTOM CTA */}
        <section className="bg-[#0F172A] py-24">
          <div className="max-w-7xl mx-auto px-6 text-center">
            <h2 className="text-4xl md:text-5xl font-headline font-extrabold text-white mb-6 tracking-tight">Ready to score your first application?</h2>
            <Link to="/solutions" className="bg-tertiary text-white px-12 py-5 rounded-xl text-xl font-bold font-headline tracking-tight hover:bg-tertiary-dim transition-all duration-300 shadow-2xl shadow-tertiary/20 flex items-center gap-4 mx-auto mb-8 active:scale-95 w-fit">
              Get Started →
            </Link>
            <p className="text-slate-400 text-lg font-medium font-body max-w-xl mx-auto mb-4">
              No credit history required. Upload a bank statement and get a risk grade in seconds.
            </p>
            <Link to="/demo" className="text-slate-500 text-xs underline">
              View Demo Profiles
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}

export default LandingPage;
