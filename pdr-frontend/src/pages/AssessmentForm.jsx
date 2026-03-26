import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import BankStatementUpload from '../components/BankStatementUpload';

function AssessmentForm() {
  // Toggle state
  const [activeForm, setActiveForm] = useState('msme');

  // Loading states
  const [msmeSubmitting, setMsmeSubmitting] = useState(false);
  const [ntcSubmitting, setNtcSubmitting] = useState(false);

  // MSME Form State
  const [msmeData, setMsmeData] = useState({
    businessName: '',
    businessType: 'Agri/Seasonal',
    businessVintageMonths: 36,
    turnoverSpike: false,
    customerConcentrationRatio: 0.35,
    repeatCustomerRevenuePct: 0.65,
    gstFilingConsistencyScore: 11,
    bankStatementFile: null,
  });

  // NTC Form State
  const [ntcData, setNtcData] = useState({
    fullName: '',
    academicBackgroundTier: 'No Schooling',
    purposeOfLoanEncoded: 'Cash Loan',
    monthlyAnnuity: '',
    annualIncome: '',
    telecomNumberVintageDays: 365,
    bankStatementFile: null,
  });

  // Repayment Burden (NTC — auto-calculate live)
  const rentWalletShare = ntcData.annualIncome > 0
    ? ((ntcData.monthlyAnnuity / (ntcData.annualIncome / 12)) * 100).toFixed(1)
    : 0;

  // MSME handlers
  const updateMsme = (field, value) => {
    setMsmeData(prev => ({ ...prev, [field]: value }));
  };

  // NTC handlers
  const updateNtc = (field, value) => {
    setNtcData(prev => ({ ...prev, [field]: value }));
  };

  // MSME Submit
  const handleMsmeSubmit = async (e) => {
    e.preventDefault();
    setMsmeSubmitting(true);
    console.log('MSME Submission:', msmeData);
    // Simulate delay for UX
    await new Promise(r => setTimeout(r, 1500));
    setMsmeSubmitting(false);
    // TODO: POST to /api/score
  };

  // NTC Submit
  const handleNtcSubmit = async (e) => {
    e.preventDefault();
    setNtcSubmitting(true);
    const payload = {
      ...ntcData,
      rent_wallet_share: parseFloat(rentWalletShare) / 100,
    };
    console.log('NTC Submission:', payload);
    // Simulate delay for UX
    await new Promise(r => setTimeout(r, 1500));
    setNtcSubmitting(false);
    // TODO: POST to /api/score
  };

  return (
    <div className="bg-slate-50 font-body text-on-surface antialiased min-h-screen">
      {/* TopAppBar Shell Component */}
      <nav className="bg-slate-50/80 backdrop-blur-xl fixed top-0 w-full z-50 shadow-sm shadow-slate-200/50 font-headline antialiased tracking-tight">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center w-full">
          <Link to="/" className="text-xl font-bold tracking-tighter text-slate-900">Paise Do Re (PDR)</Link>
          <div className="hidden md:flex items-center gap-x-8">
            <Link to="/#problem-statement" className="text-slate-500 font-medium hover:text-slate-900 transition-all duration-300">About Us</Link>
            <a className="text-slate-900 font-semibold border-b-2 border-slate-900 pb-1 hover:text-slate-900 transition-all duration-300" href="#">Solutions</a>
            <a className="text-slate-500 font-medium hover:text-slate-900 transition-all duration-300" href="#">Trust Pipeline</a>
            <a className="text-slate-500 font-medium hover:text-slate-900 transition-all duration-300" href="#">Compliance</a>
            <a className="text-slate-500 font-medium hover:text-slate-900 transition-all duration-300" href="https://github.com/lubdhak123/pdr_2" target="_blank" rel="noopener noreferrer">Documentation</a>
          </div>
          <div className="flex items-center gap-4">
            <button className="text-slate-600 font-medium hover:text-slate-900 transition-all duration-300 active:scale-95">Login</button>
            <button className="text-white px-6 py-2.5 rounded-full font-semibold active:scale-95 transition-transform duration-200 text-sm bg-emerald-600">Request Demo</button>
          </div>
        </div>
      </nav>

      <main className="pt-32 pb-24 px-4 flex flex-col items-center">
        {/* Toggle Switch */}
        <div className="flex p-1 bg-surface-container-high rounded-full w-fit mx-auto mb-8 shadow-inner border border-outline-variant/20">
          <button
            type="button"
            onClick={() => setActiveForm('msme')}
            className={`px-8 py-2 rounded-full text-xs font-bold uppercase tracking-widest cursor-pointer transition-all duration-200 ${activeForm === 'msme'
                ? 'bg-slate-900 text-white shadow-sm'
                : 'text-on-surface-variant hover:text-on-surface'
              }`}
          >
            MSME
          </button>
          <button
            type="button"
            onClick={() => setActiveForm('ntc')}
            className={`px-8 py-2 rounded-full text-xs font-bold uppercase tracking-widest cursor-pointer transition-all duration-200 ${activeForm === 'ntc'
                ? 'bg-slate-900 text-white shadow-sm'
                : 'text-on-surface-variant hover:text-on-surface'
              }`}
          >
            NTC
          </button>
        </div>

        {/* Main Assessment Card */}
        <div className="w-full max-w-[750px] space-y-8">

        {/* ==================== MSME FORM ==================== */}
        {activeForm === 'msme' && (
          <div className="w-full max-w-[750px] bg-white rounded-xl shadow-2xl border border-gray-100 overflow-hidden" key="msme" id="msme-content">
            <div className="p-10 text-center border-b border-gray-50">
              <h1 className="text-3xl font-extrabold font-headline tracking-tight text-on-surface mb-3">MSME Credit Assessment</h1>
              <p className="text-on-surface-variant max-w-lg mx-auto leading-relaxed text-sm">Precision underwriting for modern businesses. Complete the evaluation stages to generate your risk grade.</p>
            </div>

            {/* Stepper Component */}
            <form onSubmit={handleMsmeSubmit} className="p-10 space-y-12">
              {/* Step 1 */}
                  <div className="flex items-center gap-4">
                    <div className="w-1 h-8 bg-slate-900 rounded-full"></div>
                    <h2 className="text-xl font-headline font-bold text-on-surface">Step 1: Business Basics</h2>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-2">
                      <label className="block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">Business Name</label>
                      <input
                        className="w-full bg-slate-50 border-0 rounded-lg p-4 text-on-surface focus:ring-2 focus:ring-tertiary outline-none transition-all placeholder:text-outline-variant/60"
                        placeholder="ABC Manufacturing Ltd"
                        type="text"
                        value={msmeData.businessName}
                        onChange={(e) => updateMsme('businessName', e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">Business Type</label>
                      <select
                        className="w-full bg-slate-50 border-0 rounded-lg p-4 text-on-surface focus:ring-2 focus:ring-tertiary outline-none transition-all appearance-none cursor-pointer"
                        value={msmeData.businessType}
                        onChange={(e) => updateMsme('businessType', e.target.value)}
                      >
                        <option>Agri/Seasonal</option>
                        <option>Manufacturer</option>
                        <option>Service Provider</option>
                        <option>Retailer/Kirana</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <label className="block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">Business Vintage (Months)</label>
                      <div className="relative">
                        <input
                          className="w-full bg-slate-50 border-0 rounded-lg p-4 text-on-surface focus:ring-2 focus:ring-tertiary outline-none transition-all"
                          max="240"
                          min="0"
                          type="number"
                          value={msmeData.businessVintageMonths}
                          onChange={(e) => updateMsme('businessVintageMonths', parseInt(e.target.value) || 0)}
                        />
                        <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs text-on-surface-variant font-medium">months</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between bg-surface-container-low p-4 rounded-lg">
                      <div className="space-y-1">
                        <label className="block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">Turnover Spike</label>
                        <p className="text-xs text-on-surface-variant">Did revenue spike &gt;25% in last quarter?</p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          className="sr-only peer"
                          type="checkbox"
                          checked={msmeData.turnoverSpike}
                          onChange={(e) => updateMsme('turnoverSpike', e.target.checked)}
                        />
                        <div className="w-11 h-6 bg-outline-variant/30 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-slate-900"></div>
                      </label>
                    </div>
                  </div>

                  {/* Step 2 */}
                  <div className="pt-8 border-t border-outline-variant/10 space-y-8">
                    <div className="flex items-center gap-4">
                      <div className="w-1 h-8 bg-slate-900 rounded-full"></div>
                      <h2 className="text-xl font-headline font-bold text-on-surface">Step 2: Network &amp; Customers</h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                      <div className="space-y-2">
                        <label className="block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">Customer Concentration Ratio</label>
                        <input
                          className="w-full bg-slate-50 border-0 rounded-lg p-4 text-on-surface focus:ring-2 focus:ring-tertiary outline-none"
                          max="1"
                          min="0"
                          placeholder="0.35"
                          step="0.01"
                          type="number"
                          value={msmeData.customerConcentrationRatio}
                          onChange={(e) => updateMsme('customerConcentrationRatio', parseFloat(e.target.value) || 0)}
                        />
                        <p className="text-[11px] text-on-surface-variant/80 italic font-medium leading-tight">Example: 0.35 = Top customer is 35% of revenue</p>
                      </div>
                      <div className="space-y-2">
                        <label className="block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">Repeat Customer Revenue (%)</label>
                        <input
                          className="w-full bg-slate-50 border-0 rounded-lg p-4 text-on-surface focus:ring-2 focus:ring-tertiary outline-none"
                          max="1"
                          min="0"
                          placeholder="0.65"
                          step="0.01"
                          type="number"
                          value={msmeData.repeatCustomerRevenuePct}
                          onChange={(e) => updateMsme('repeatCustomerRevenuePct', parseFloat(e.target.value) || 0)}
                        />
                        <p className="text-[11px] text-on-surface-variant/80 italic font-medium leading-tight">Example: 0.65 = 65% from repeat customers</p>
                      </div>
                    </div>
                  </div>

                  {/* Step 3 */}
                  <div className="pt-8 border-t border-outline-variant/10 space-y-8">
                    <div className="flex items-center gap-4">
                      <div className="w-1 h-8 bg-slate-900 rounded-full"></div>
                      <h2 className="text-xl font-headline font-bold text-on-surface">Step 3: Compliance</h2>
                    </div>
                    <div className="space-y-2 max-w-md">
                      <label className="block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">GST Filing Consistency Score</label>
                      <p className="text-xs text-on-surface-variant mb-2">Out of last 12 months, how many filed on time?</p>
                      <input
                        className="w-full bg-slate-50 border-0 rounded-lg p-4 text-on-surface focus:ring-2 focus:ring-tertiary outline-none"
                        max="12"
                        min="0"
                        type="number"
                        value={msmeData.gstFilingConsistencyScore}
                        onChange={(e) => updateMsme('gstFilingConsistencyScore', parseInt(e.target.value) || 0)}
                      />
                    </div>
                  </div>

              {/* Step 4: Bank Data Upload */}
              <section className="pt-8 border-t border-outline-variant/10 space-y-6">
                <div className="flex items-center gap-4">
                  <div className="w-1 h-8 bg-slate-900 rounded-full"></div>
                  <h2 className="text-xl font-headline font-bold text-on-surface">Bank Data Upload</h2>
                </div>
                <BankStatementUpload
                  formType="msme"
                  onFileSelect={(file) => updateMsme('bankStatementFile', file)}
                />
                <div className="bg-blue-50/50 border border-blue-100 p-4 rounded-lg flex items-start gap-3">
                  <span className="material-symbols-outlined text-blue-600 text-xl">info</span>
                  <div className="space-y-1">
                    <p className="text-[11px] font-bold uppercase tracking-widest text-blue-700">Engine Auto-Calculation</p>
                    <p className="text-[11px] text-blue-800 leading-relaxed">Uploading will <span className="font-bold">AUTO-CALCULATE</span>: Revenue Growth, Seasonality, Cashflow Ratios, Volatility, Invoice Delays, Vendor Discipline, and GST Variance.</p>
                  </div>
                </div>
              </section>
            </form>
            </div>
          )}

          {/* Action Area */}
          {activeForm === 'msme' && (
            <div className="w-full max-w-[750px] mt-10 space-y-8">
              <div className="text-center">
                <p className="text-xs text-on-surface-variant mb-6">Your data is processed according to global privacy and credit standards.</p>
                <button
                  onClick={handleMsmeSubmit}
                  className="w-full py-5 text-white rounded-xl font-bold text-lg hover:scale-[0.99] transition-all duration-200 flex items-center justify-center gap-3 shadow-lg bg-emerald-600"
                >
                  ACCESS CREDIT RISK <span className="material-symbols-outlined">trending_up</span>
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm flex flex-col items-center text-center space-y-2">
                  <span className="material-symbols-outlined text-tertiary">bolt</span>
                  <h4 className="text-xs font-bold uppercase tracking-widest">Real-Time Analysis</h4>
                </div>
                <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm flex flex-col items-center text-center space-y-2">
                  <span className="material-symbols-outlined text-tertiary">balance</span>
                  <h4 className="text-xs font-bold uppercase tracking-widest">Risk Weighting</h4>
                </div>
                <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm flex flex-col items-center text-center space-y-2">
                  <span className="material-symbols-outlined text-tertiary">description</span>
                  <h4 className="text-xs font-bold uppercase tracking-widest">Instant Report</h4>
                </div>
              </div>
              <div className="flex justify-center gap-12 pt-4">
                <button className="text-xs font-bold uppercase tracking-widest text-on-surface-variant hover:text-primary transition-colors underline underline-offset-4">Save Progress</button>
                <button className="text-xs font-bold uppercase tracking-widest text-on-surface-variant hover:text-primary transition-colors underline underline-offset-4">Print Draft</button>
              </div>
            </div>
          )}

        {/* ==================== NTC FORM ==================== */}
        {activeForm === 'ntc' && (
          <div className="w-full max-w-[750px] bg-white rounded-xl shadow-2xl border border-gray-100 overflow-hidden" key="ntc" id="ntc-content">
            <div className="p-10 text-center border-b border-gray-50">
              <h1 className="text-3xl font-extrabold font-headline tracking-tight text-on-surface mb-3">New To Credit Assessment</h1>
              <p className="text-on-surface-variant max-w-md mx-auto leading-relaxed">Credit scoring for individuals with limited financial history. Predictive analysis based on behavioral data.</p>
            </div>

            <form onSubmit={handleNtcSubmit} className="p-10 space-y-12">
              {/* Step 1: Personal Background */}
              <div className="flex items-center gap-4">
                <div className="w-1 h-8 bg-slate-900 rounded-full"></div>
                <h2 className="text-xl font-headline font-bold text-on-surface">Step 1: Personal Background</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-2">
                  <label className="block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">Full Name</label>
                  <input
                    className="w-full bg-slate-50 border-0 rounded-lg p-4 text-on-surface focus:ring-2 focus:ring-tertiary outline-none transition-all placeholder:text-outline-variant/60"
                    placeholder="John Doe"
                    type="text"
                    value={ntcData.fullName}
                    onChange={(e) => updateNtc('fullName', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">Education Level</label>
                  <select
                    className="w-full bg-slate-50 border-0 rounded-lg p-4 text-on-surface focus:ring-2 focus:ring-tertiary outline-none transition-all appearance-none cursor-pointer"
                    value={ntcData.academicBackgroundTier}
                    onChange={(e) => updateNtc('academicBackgroundTier', e.target.value)}
                  >
                    <option>No Schooling</option>
                    <option>School</option>
                    <option>Diploma</option>
                    <option>Graduate</option>
                    <option>Postgraduate</option>
                  </select>
                </div>
              </div>

              {/* Step 2: Loan Details */}
              <div className="pt-8 border-t border-outline-variant/10 space-y-8">
                <div className="flex items-center gap-4">
                  <div className="w-1 h-8 bg-slate-900 rounded-full"></div>
                  <h2 className="text-xl font-headline font-bold text-on-surface">Step 2: Loan Details</h2>
                </div>
                <div className="space-y-6">
                  {/* Loan Type Toggle */}
                  <div className="space-y-2">
                    <label className="block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">Loan Type</label>
                    <div className="flex p-1 bg-surface-container-low rounded-lg w-fit border border-outline-variant/20">
                      <button
                        type="button"
                        onClick={() => updateNtc('purposeOfLoanEncoded', 'Cash Loan')}
                        className={`px-6 py-2 rounded-md text-[10px] font-bold uppercase tracking-widest transition-colors ${ntcData.purposeOfLoanEncoded === 'Cash Loan'
                            ? 'bg-slate-900 text-white'
                            : 'text-on-surface-variant hover:bg-surface-container-high'
                          }`}
                      >
                        Cash Loan
                      </button>
                      <button
                        type="button"
                        onClick={() => updateNtc('purposeOfLoanEncoded', 'Revolving Credit')}
                        className={`px-6 py-2 rounded-md text-[10px] font-bold uppercase tracking-widest transition-colors ${ntcData.purposeOfLoanEncoded === 'Revolving Credit'
                            ? 'bg-slate-900 text-white'
                            : 'text-on-surface-variant hover:bg-surface-container-high'
                          }`}
                      >
                        Revolving Credit
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-2">
                      <label className="block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">Monthly Annuity ₹</label>
                      <input
                        className="w-full bg-slate-50 border-0 rounded-lg p-4 text-on-surface focus:ring-2 focus:ring-tertiary outline-none"
                        placeholder="5000"
                        type="number"
                        value={ntcData.monthlyAnnuity}
                        onChange={(e) => updateNtc('monthlyAnnuity', e.target.value)}
                      />
                      <p className="text-[11px] text-on-surface-variant/80 italic font-medium leading-tight">Your monthly loan repayment amount</p>
                    </div>
                    <div className="space-y-2">
                      <label className="block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">Annual Income ₹</label>
                      <input
                        className="w-full bg-slate-50 border-0 rounded-lg p-4 text-on-surface focus:ring-2 focus:ring-tertiary outline-none"
                        placeholder="600000"
                        type="number"
                        value={ntcData.annualIncome}
                        onChange={(e) => updateNtc('annualIncome', e.target.value)}
                      />
                      <p className="text-[11px] text-on-surface-variant/80 italic font-medium leading-tight">Used to calculate repayment burden</p>
                    </div>
                  </div>

                  {/* Repayment Burden — auto-calculated */}
                  <div className="bg-surface-container-high/40 p-6 rounded-xl border border-outline-variant/10 flex items-center justify-between">
                    <div className="space-y-1">
                      <label className="block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">Repayment Burden</label>
                      <p className="text-xs text-on-surface-variant">Auto-calculated based on annuity and income</p>
                    </div>
                    <div className="text-2xl font-headline font-extrabold text-slate-900">{rentWalletShare}%</div>
                  </div>
                </div>
              </div>

              {/* Step 3: Telecom & Identity */}
              <div className="pt-8 border-t border-outline-variant/10 space-y-8">
                <div className="flex items-center gap-4">
                  <div className="w-1 h-8 bg-slate-900 rounded-full"></div>
                  <h2 className="text-xl font-headline font-bold text-on-surface">Step 3: Telecom &amp; Identity</h2>
                </div>
                <div className="space-y-2 max-w-md">
                  <label className="block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">Phone Number Age</label>
                  <div className="relative">
                    <input
                      className="w-full bg-slate-50 border-0 rounded-lg p-4 text-on-surface focus:ring-2 focus:ring-tertiary outline-none"
                      placeholder="365"
                      type="number"
                      value={ntcData.telecomNumberVintageDays}
                      onChange={(e) => updateNtc('telecomNumberVintageDays', parseInt(e.target.value) || 0)}
                    />
                    <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs text-on-surface-variant font-medium">days</span>
                  </div>
                  <p className="text-[11px] text-on-surface-variant/80 italic font-medium mt-2">Days since last phone number change</p>
                </div>
              </div>

              {/* Step 4: Bank Data Upload */}
              <section className="pt-8 border-t border-outline-variant/10 space-y-6">
                <div className="flex items-center gap-4">
              <div className="w-1 h-8 bg-slate-900 rounded-full"></div>
              <h2 className="text-xl font-headline font-bold text-on-surface">Step 4: Bank Data Upload</h2>
                </div>
                <BankStatementUpload
              formType="ntc"
              onFileSelect={(file) => updateNtc('bankStatementFile', file)}
                />
              </section>
            </form>
            </div>
          )}

          {/* Action Area */}
          {activeForm === 'ntc' && (
            <div className="w-full max-w-[750px] mt-10 space-y-8">
              <div className="text-center">
                <p className="text-xs text-on-surface-variant mb-6">Your data is processed according to global privacy and credit standards.</p>
                <button
                  onClick={handleNtcSubmit}
                  className="w-full py-5 text-white rounded-xl font-bold text-lg hover:scale-[0.99] transition-all duration-200 flex items-center justify-center gap-3 shadow-lg bg-emerald-600"
                >
                  ACCESS CREDIT RISK <span className="material-symbols-outlined">trending_up</span>
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm flex flex-col items-center text-center space-y-2">
                  <span className="material-symbols-outlined text-tertiary">bolt</span>
                  <h4 className="text-xs font-bold uppercase tracking-widest">Real-Time Analysis</h4>
                </div>
                <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm flex flex-col items-center text-center space-y-2">
                  <span className="material-symbols-outlined text-tertiary">balance</span>
                  <h4 className="text-xs font-bold uppercase tracking-widest">Risk Weighting</h4>
                </div>
                <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm flex flex-col items-center text-center space-y-2">
                  <span className="material-symbols-outlined text-tertiary">description</span>
                  <h4 className="text-xs font-bold uppercase tracking-widest">Instant Report</h4>
                </div>
              </div>
              <div className="flex justify-center gap-12 pt-4">
                <button className="text-xs font-bold uppercase tracking-widest text-on-surface-variant hover:text-primary transition-colors underline underline-offset-4">Save Progress</button>
                <button className="text-xs font-bold uppercase tracking-widest text-on-surface-variant hover:text-primary transition-colors underline underline-offset-4">Print Draft</button>
              </div>
            </div>
          )}


        </div>
      </main>

      {/* Bottom Navigation (Mobile Only) */}
      <nav className="md:hidden fixed bottom-0 w-full bg-white flex justify-around items-center py-3 z-50 shadow-[0_-2px_10px_rgba(0,0,0,0.05)] border-t border-slate-100">
        <Link to="/" className="flex flex-col items-center text-on-surface-variant">
          <span className="material-symbols-outlined">dashboard</span>
          <span className="text-[10px] mt-1">Home</span>
        </Link>
        <div className="flex flex-col items-center text-slate-900 font-bold">
          <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>assignment</span>
          <span className="text-[10px] mt-1">Assess</span>
        </div>
        <div className="flex flex-col items-center text-on-surface-variant">
          <span className="material-symbols-outlined">query_stats</span>
          <span className="text-[10px] mt-1">Stats</span>
        </div>
        <div className="flex flex-col items-center text-on-surface-variant">
          <span className="material-symbols-outlined">account_circle</span>
          <span className="text-[10px] mt-1">Profile</span>
        </div>
      </nav>
    </div>
  );
}

export default AssessmentForm;
