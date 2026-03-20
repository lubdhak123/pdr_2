import React, { useRef, useEffect } from 'react';
import './Results.css';

const PROFILE_DETAILS = {
  'DEMO_001': { name: 'Rajesh Sharma', city: 'Bengaluru', persona: 'Clean IT Contractor' },
  'DEMO_002': { name: 'Mohammed Farouk', city: 'Delhi', persona: 'Wash Trader' },
  'DEMO_003': { name: 'Sukhwinder Singh', city: 'Ludhiana', persona: 'Seasonal Farmer' },
  'DEMO_004': { name: 'Priya Patel', city: 'Surat', persona: 'Struggling Kirana' },
  'DEMO_005': { name: 'Arjun Nair', city: 'Kochi', persona: 'NRI Remittance Receiver' }
};

export default function Results({ result, onBack }) {
  if (!result) return null;

  const profile = result.user_id ? PROFILE_DETAILS[result.user_id]
    : Object.values(PROFILE_DETAILS)[0];

  const getOutcomeClass = (outcome) => {
    switch (outcome) {
      case 'APPROVED': return 'out-approved';
      case 'APPROVED WITH CONDITIONS': return 'out-cond';
      case 'MANUAL REVIEW': return 'out-review';
      case 'REJECTED': return 'out-rejected';
      default: return '';
    }
  };

  const getSourceClass = (source) => {
    return source === 'pre_layer' ? 'src-pre' : 'src-model';
  };

  const formatProb = (prob) => {
    if (prob === null || prob === undefined) return 'N/A — Rule override';
    return `Default Probability: ${(prob * 100).toFixed(1)}%`;
  };

  const hasShap = result.shap_reasons && result.shap_reasons.length > 0;

  const keyFeatures = [
    { key: 'bounced_transaction_count', label: 'Bounce Charges' },
    { key: 'utility_payment_consistency', label: 'Utility Bills Paid' },
    { key: 'cash_withdrawal_dependency', label: 'Cash Withdrawal' },
    { key: 'min_balance_violation_count', label: 'Min Balance Violations' },
    { key: 'gst_filing_consistency_score', label: 'GST Filings' },
    { key: 'gst_to_bank_variance', label: 'GST Variance' },
    { key: 'customer_concentration_ratio', label: 'Client Concentration' },
    { key: 'operating_cashflow_ratio', label: 'Cashflow Ratio' }
  ];

  const formatFeatureValue = (key, val) => {
    if (val === null || val === undefined) return 'N/A';
    if (key === 'p2p_circular_loop_flag') return val === 1 ? 'Yes' : 'No';
    if (key === 'cash_withdrawal_dependency') return `${(val * 100).toFixed(0)}%`;
    if (Number.isInteger(val)) return val;
    if (typeof val === 'number') return val.toFixed(2);
    return val;
  };

  const getShapImpactClass = (impactStr) => {
    const s = impactStr.toLowerCase();
    if (s.includes('very high')) return 'shap-very-high';
    if (s.includes('high')) return 'shap-high';
    return 'shap-medium';
  };

  const timelineChartRef = useRef(null);
  const radarChartRef = useRef(null);

  useEffect(() => {
    if (!result) return;
    const { features = {} } = result;

    if (timelineChartRef.current?.chartInstance) {
      timelineChartRef.current.chartInstance.destroy();
    }
    if (radarChartRef.current?.chartInstance) {
      radarChartRef.current.chartInstance.destroy();
    }

    // --- CHART 1: Timeline ---
    const cr = features.operating_cashflow_ratio || 1;
    const vol = features.cashflow_volatility || 0;
    const seas = features.revenue_seasonality_index || 0;

    const baseExp = 50000;
    const baseInc = cr * baseExp;

    const months = ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'];
    const incomeData = [];
    const expData = [];

    months.forEach((m, i) => {
      const seasonFactor = 1 + Math.sin(i) * seas;
      const rand = (i % 3 === 0 ? 1 : i % 2 === 0 ? -1 : 0.5);
      const volFactor = (vol / baseInc) * rand * 0.1 || 0; 
      const inc = baseInc * seasonFactor * (1 + volFactor);
      const exp = baseExp * (1 + volFactor * 0.5);
      incomeData.push(Math.round(inc));
      expData.push(Math.round(exp));
    });

    if (timelineChartRef.current) {
      const ctxTime = timelineChartRef.current.getContext('2d');
      timelineChartRef.current.chartInstance = new window.Chart(ctxTime, {
        type: 'bar',
        data: {
          labels: months,
          datasets: [
            { label: 'Income', data: incomeData, backgroundColor: '#22c55e' },
            { label: 'Expenses', data: expData, backgroundColor: '#ef4444' }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } },
            tooltip: { mode: 'index', intersect: false }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: { font: { size: 10 }, callback: v => '₹' + (v / 1000) + 'k' }
            }
          }
        }
      });
    }

    // --- CHART 2: Radar ---
    const p_util = features.utility_payment_consistency || 0;
    const p_bounce = features.bounced_transaction_count || 0;
    const paymentScore = ((Math.min(p_util, 12) / 12) * 0.4 + (1 - Math.min(p_bounce / 5, 1)) * 0.6) * 100;

    const l_cash = features.cash_withdrawal_dependency || 0;
    const l_minbal = features.min_balance_violation_count || 0;
    const l_emerg = features.emergency_buffer_months || 0;
    const liquidityScore = ((1 - Math.min(l_cash, 1)) * 0.4 + (1 - Math.min(l_minbal / 5, 1)) * 0.4 + Math.min(l_emerg / 3, 1) * 0.2) * 100;

    const i_vin = features.telecom_number_vintage_days || 0;
    const i_acad = features.academic_background_tier || 0;
    const identityScore = (Math.min(i_vin / 2000, 1) * 0.6 + (i_acad !== 0 ? 0.4 : 0)) * 100;

    const m_cr = features.operating_cashflow_ratio || 0;
    const m_vol = features.cashflow_volatility || 0;
    const m_vin = features.business_vintage_months || 0;
    const msmeScore = (Math.min(m_cr / 3, 1) * 0.5 + (1 - Math.min(m_vol / 50000, 1)) * 0.3 + Math.min(m_vin / 60, 1) * 0.2) * 100;

    const n_conc = features.customer_concentration_ratio || 0;
    const n_rep = features.repeat_customer_revenue_pct || 0;
    const n_delay = features.avg_invoice_payment_delay || 0;
    const networkScore = ((1 - n_conc) * 0.5 + n_rep * 0.3 + (1 - Math.min(n_delay / 30, 1)) * 0.2) * 100;

    const c_p2p = features.p2p_circular_loop_flag !== undefined ? features.p2p_circular_loop_flag : 0;
    const c_var = features.gst_to_bank_variance || 0;
    const c_gst = features.gst_filing_consistency_score || 0;
    const complianceScore = ((1 - c_p2p) * 0.4 + (1 - Math.min(c_var, 1)) * 0.3 + Math.min(c_gst / 12, 1) * 0.3) * 100;

    const scores = [
      Math.max(0, Math.min(100, paymentScore)),
      Math.max(0, Math.min(100, liquidityScore)),
      Math.max(0, Math.min(100, identityScore)),
      Math.max(0, Math.min(100, msmeScore)),
      Math.max(0, Math.min(100, networkScore)),
      Math.max(0, Math.min(100, complianceScore))
    ].map(s => Math.round(s));

    const grade = (result.grade || 'C').toUpperCase();
    let bg = 'rgba(146, 64, 14, 0.2)';
    let bc = '#92400e';
    if (grade === 'A') { bg = 'rgba(22, 101, 52, 0.2)'; bc = '#166534'; }
    else if (grade === 'B') { bg = 'rgba(29, 78, 216, 0.2)'; bc = '#1d4ed8'; }
    else if (grade === 'D') { bg = 'rgba(154, 52, 18, 0.2)'; bc = '#9a3412'; }
    else if (grade === 'E') { bg = 'rgba(153, 27, 27, 0.2)'; bc = '#991b1b'; }

    if (radarChartRef.current) {
      const ctxRadar = radarChartRef.current.getContext('2d');
      radarChartRef.current.chartInstance = new window.Chart(ctxRadar, {
        type: 'radar',
        data: {
          labels: ['Payment Discipline', 'Liquidity Health', 'Identity Stability', 'MSME Health', 'Network Risk', 'Compliance'],
          datasets: [{
            label: 'Score',
            data: scores,
            backgroundColor: bg,
            borderColor: bc,
            borderWidth: 2,
            pointBackgroundColor: bc
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: (ctx) => `${ctx.raw}/100` } }
          },
          scales: {
            r: {
              min: 0, max: 100,
              ticks: { display: false },
              pointLabels: { font: { size: 10 } }
            }
          }
        }
      });
    }
  }, [result]);

  const buildVerdictCard = (result, profile) => {
    const { features = {} } = result;
    const name = profile?.name ? profile.name.split(' ')[0] : 'The applicant';

    let icon = '✅';
    if (result.outcome === 'APPROVED WITH CONDITIONS') icon = '⚠️';
    else if (result.outcome === 'MANUAL REVIEW') icon = '🔍';
    else if (result.outcome === 'REJECTED') icon = '❌';

    let headline = '';
    let paragraph = '';
    const grade = (result.grade || 'C').toUpperCase();

    if (grade === 'A') {
      headline = 'Strong identity and zero payment failures';
      paragraph = `${name} has maintained ${features.bounced_transaction_count || 0} bounce charges over 6 months with consistent utility bill payments. His SIM card has been active for ${Math.round(features.telecom_number_vintage_days || 0).toLocaleString()} days — a strong identity anchor. ${features.p2p_circular_loop_flag ? 'Some' : 'No'} circular fund flows detected.`;
    } else if (grade === 'E' || result.outcome === 'REJECTED') {
      headline = 'High risk indicators and network fraud signals';
      paragraph = `${name}'s account shows severe risk flags. There are ${features.min_balance_violation_count || 0} instances of zero balance and suspicious cash withdrawal patterns (${Math.round((features.cash_withdrawal_dependency || 0) * 100)}% dependence). ${features.p2p_circular_loop_flag ? 'Circular P2P loops strongly suggest organized manipulation.' : ''}`;
    } else if (grade === 'D') {
      headline = 'Liquidity stress and payment irregularities';
      paragraph = `${name} is experiencing obvious liquidity constraints with ${features.min_balance_violation_count || 0} minimum balance drops. The high variance in GST-to-bank credits (${Math.round((features.gst_to_bank_variance || 0) * 100)}%) creates uncertainty around actual revenue.`;
    } else {
      if (profile?.persona?.toLowerCase().includes('seasonal') || features.operating_cashflow_ratio > 1.2) {
        headline = 'Reliable history with seasonal income gaps';
        paragraph = `${name} has an operating cashflow ratio of ${(features.operating_cashflow_ratio || 0).toFixed(2)}, showing good surpluses during in-season months. However, utility payment consistency drops to ${Math.round((features.utility_payment_consistency || 0) * 100)}% off-season.`;
      } else {
        headline = 'Moderate activity with some financial strain';
        paragraph = `${name} maintains a reasonable profile but exhibits ${features.bounced_transaction_count || 0} recent bounce charges. Identity is stable (SIM active ${Math.round(features.telecom_number_vintage_days || 0)} days), but cash withdrawal levels (${Math.round((features.cash_withdrawal_dependency || 0) * 100)}%) require monitoring.`;
      }
    }

    let topShaps = [];
    if (result.shap_reasons && result.shap_reasons.length > 0) {
      topShaps = [...result.shap_reasons]
        .sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value))
        .slice(0, 3);
    }

    const maxShap = topShaps.length > 0 ? Math.max(...topShaps.map(s => Math.abs(s.shap_value))) : 1;
    const topShapData = topShaps.map(s => ({
      label: s.reason,
      direction: s.direction,
      width: Math.max(5, (Math.abs(s.shap_value) / maxShap) * 100)
    }));

    return { icon, headline, paragraph, topShapData };
  };

  const verdict = buildVerdictCard(result, profile);

  const maxAbsShap = hasShap ? Math.max(...result.shap_reasons.map(s => Math.abs(s.shap_value))) : 1;
  const normalizedShaps = hasShap ? result.shap_reasons.map(s => ({
    ...s,
    normalizedPct: (Math.abs(s.shap_value) / maxAbsShap) * 100
  })) : [];

  const getFeatureStatus = (key, val) => {
    switch (key) {
      case 'bounced_transaction_count':
        if (val === 0) return { label: 'Strong', icon: '✅', cls: 'chip-strong' };
        if (val <= 2) return { label: 'Watch', icon: '⚠️', cls: 'chip-watch' };
        return { label: 'Risk', icon: '🔴', cls: 'chip-risk' };
      case 'utility_payment_consistency':
        if (val >= 6) return { label: 'Strong', icon: '✅', cls: 'chip-strong' };
        if (val >= 3) return { label: 'Watch', icon: '⚠️', cls: 'chip-watch' };
        return { label: 'Risk', icon: '🔴', cls: 'chip-risk' };
      case 'cash_withdrawal_dependency':
        if (val < 0.2) return { label: 'Strong', icon: '✅', cls: 'chip-strong' };
        if (val <= 0.5) return { label: 'Watch', icon: '⚠️', cls: 'chip-watch' };
        return { label: 'Risk', icon: '🔴', cls: 'chip-risk' };
      case 'min_balance_violation_count':
        if (val === 0) return { label: 'Strong', icon: '✅', cls: 'chip-strong' };
        if (val <= 2) return { label: 'Watch', icon: '⚠️', cls: 'chip-watch' };
        return { label: 'Risk', icon: '🔴', cls: 'chip-risk' };
      case 'gst_filing_consistency_score':
        if (val >= 6) return { label: 'Strong', icon: '✅', cls: 'chip-strong' };
        if (val >= 3) return { label: 'Watch', icon: '⚠️', cls: 'chip-watch' };
        return { label: 'Risk', icon: '🔴', cls: 'chip-risk' };
      case 'telecom_number_vintage_days':
        if (val > 1000) return { label: 'Strong', icon: '✅', cls: 'chip-strong' };
        if (val >= 500) return { label: 'Watch', icon: '⚠️', cls: 'chip-watch' };
        return { label: 'Risk', icon: '🔴', cls: 'chip-risk' };
      case 'gst_to_bank_variance':
        if (val < 0.2) return { label: 'Strong', icon: '✅', cls: 'chip-strong' };
        if (val <= 0.5) return { label: 'Watch', icon: '⚠️', cls: 'chip-watch' };
        return { label: 'Risk', icon: '🔴', cls: 'chip-risk' };
      case 'p2p_circular_loop_flag':
        if (val === 0) return { label: 'Strong', icon: '✅', cls: 'chip-strong' };
        return { label: 'Risk', icon: '🔴', cls: 'chip-risk' };
      case 'customer_concentration_ratio':
        if (val < 0.5) return { label: 'Strong', icon: '✅', cls: 'chip-strong' };
        if (val <= 0.8) return { label: 'Watch', icon: '⚠️', cls: 'chip-watch' };
        return { label: 'Risk', icon: '🔴', cls: 'chip-risk' };
      case 'operating_cashflow_ratio':
        if (val > 1.5) return { label: 'Strong', icon: '✅', cls: 'chip-strong' };
        if (val >= 1) return { label: 'Watch', icon: '⚠️', cls: 'chip-watch' };
        return { label: 'Risk', icon: '🔴', cls: 'chip-risk' };
      default:
        return null;
    }
  };

  const tooltips = {
    bounced_transaction_count: "Number of times payments failed due to insufficient funds",
    utility_payment_consistency: "Number of utility bills (electricity/water/gas) paid on time",
    cash_withdrawal_dependency: "% of total debits taken out as cash — high values suggest off-book activity",
    min_balance_violation_count: "Times the account balance dropped to zero or below minimum",
    telecom_number_vintage_days: "How long the borrower's mobile number has been active",
    gst_to_bank_variance: "Gap between declared GST turnover and actual bank credits — flags inflation",
    p2p_circular_loop_flag: "Detects money cycling between same parties — fraud signal",
    operating_cashflow_ratio: "Income vs expenses ratio — above 1.5 means healthy surplus",
    gst_filing_consistency_score: "Number of months GST returns were filed consistently",
    customer_concentration_ratio: "How dependent the business is on a single client — 1.0 means only one customer"
  };

  return (
    <>
      <div className="results-container">
        <button className="r-back-btn" onClick={onBack}>&larr; Back to profiles</button>

        <div className="r-header">
          <div className="r-header-left">
            <div className="r-label">CREDIT DECISION</div>
            <div className="r-name">{profile?.name || result.user_id}</div>
            <div className="r-persona">{profile?.persona || 'Unknown'} · {profile?.city || 'Unknown'}</div>
            <div className={`r-outcome ${getOutcomeClass(result.outcome)}`}>
              {result.outcome}
            </div>
          </div>
          <div className="r-header-right">
            <div className={`r-grade r-grade-${(result.grade || 'C').toLowerCase()}`}>
              {result.grade}
            </div>
            <div className="r-grade-label">Risk Grade</div>
          </div>
        </div>

        <div className="r-divider"></div>

        <div className={`r-source-banner ${getSourceClass(result.decision_source)}`}>
          <div className="r-source-left">
            <span className="r-source-label">
              {result.decision_source === 'pre_layer' ? 'Rule Engine Decision' : 'ML Model Decision'}
            </span>
            <span className="r-source-desc">
              {result.decision_source === 'pre_layer'
                ? 'Triggered by hard business rule — no model consultation required'
                : 'Scored by XGBoost model with SHAP explainability'}
            </span>
          </div>
          <div className="r-source-right">
            {formatProb(result.default_probability)}
          </div>
        </div>

        <div className="r-verdict-card">
          <div className="r-verdict-top">
            <div className="r-verdict-icon">{verdict.icon}</div>
            <div className="r-verdict-text">
              <h3 className="r-verdict-headline">{verdict.headline}</h3>
              <p className="r-verdict-para">{verdict.paragraph}</p>
            </div>
          </div>
          {verdict.topShapData && verdict.topShapData.length > 0 && (
            <div className="r-verdict-mini-chart">
              <div className="mini-chart-label">Top Decision Drivers</div>
              {verdict.topShapData.map((d, i) => (
                <div className="mini-chart-row" key={i}>
                  <div className="mini-chart-name">{d.label}</div>
                  <div className="mini-chart-bar-area">
                    {d.direction === 'strength' ? (
                      <div className="mini-bar-strength" style={{ width: `${d.width}%` }}></div>
                    ) : (
                      <div className="mini-bar-risk" style={{ width: `${d.width}%`, marginLeft: 'auto' }}></div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="r-section">
          <h2 className="r-section-title" style={{ marginBottom: '4px' }}>Decision Intelligence</h2>
          <div className="r-chart-subtitle">Derived from behavioral signals across 6 pillars</div>
          <div className="r-charts-grid">
            <div className="r-chart-box">
              <div className="r-chart-title">Monthly Cashflow Pattern</div>
              <div style={{ height: '220px', width: '100%' }}>
                <canvas ref={timelineChartRef}></canvas>
              </div>
            </div>
            <div className="r-chart-box" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div className="r-chart-title" style={{ alignSelf: 'flex-start' }}>PDR Risk Radar</div>
              <div style={{ height: '280px', width: '100%', maxWidth: '480px' }}>
                <canvas ref={radarChartRef}></canvas>
              </div>
            </div>
          </div>
        </div>

        {hasShap && (
          <div className="r-section">
            <h2 className="r-section-title">Behavioral Signal Breakdown</h2>
            <div className="shap-legend">
              <div className="legend-item"><div className="r-shap-dot dot-strength"></div> Pushes toward approval</div>
              <div className="legend-item"><div className="r-shap-dot dot-risk"></div> Pushes toward rejection</div>
            </div>
            <div className="r-shap-list">
              {normalizedShaps.map((shap, idx) => (
                <div className="r-shap-row" key={idx}>
                  <div className={`r-shap-dot ${shap.direction === 'risk' ? 'dot-risk' : 'dot-strength'}`}></div>
                  <div className="r-shap-mid">
                    <div className="r-shap-reason">{shap.reason}</div>
                    <div className="r-shap-feature">{shap.feature}</div>
                  </div>
                  <div className="r-shap-bar-wrapper">
                    {shap.direction === 'strength' ? (
                      <div className="r-shap-bar bar-strength" style={{ width: `${shap.normalizedPct}%`, left: 0 }}></div>
                    ) : (
                      <div className="r-shap-bar bar-risk" style={{ width: `${shap.normalizedPct}%`, right: 0 }}></div>
                    )}
                  </div>
                  <div className={`r-shap-impact ${getShapImpactClass(shap.impact)}`}>
                    {shap.impact}
                  </div>
                  <div className={`r-shap-value ${shap.direction === 'risk' ? 'val-risk' : 'val-strength'}`}>
                    {(shap.direction === 'risk' && shap.shap_value > 0 ? '+' : '')}{shap.shap_value.toFixed(4)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="r-section">
          <h2 className="r-section-title">Key Feature Values</h2>
          <div className="r-feature-grid">
            {keyFeatures.map((kf, idx) => {
              const val = result.features?.[kf.key];
              const status = getFeatureStatus(kf.key, val);

              return (
                <div className="r-feature-cell tooltip-container" key={idx}>
                  <div className="r-f-top">
                    <div className="r-f-label">{kf.label}</div>
                    {status && (
                      <div className={`r-f-chip ${status.cls}`}>
                        {status.label}
                      </div>
                    )}
                  </div>
                  <div className="r-f-value">
                    {formatFeatureValue(kf.key, val)}
                  </div>
                  <div className="tooltip-text">{tooltips[kf.key]}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Extra spacing for sticky footer */}
        <div style={{ height: '100px' }}></div>
      </div>

      <div className="r-footer">
        <div className="r-footer-left">PDR · Alternative Credit Intelligence</div>
        <div className="r-footer-right">
          <button className="r-btn-outline" onClick={onBack}>&larr; Score another profile</button>
          <button className="r-btn-solid">Export Decision</button>
        </div>
      </div>
    </>
  );
}


