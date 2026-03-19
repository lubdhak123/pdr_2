import React from 'react';
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
    : Object.values(PROFILE_DETAILS)[0]; // Fallback

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
    { key: 'utility_payment_consistency', label: 'Utility Payments' },
    { key: 'cash_withdrawal_dependency', label: 'Cash Withdrawal' },
    { key: 'min_balance_violation_count', label: 'Min Balance Violations' },
    { key: 'telecom_number_vintage_days', label: 'SIM Vintage (days)' },
    { key: 'gst_to_bank_variance', label: 'GST Variance' },
    { key: 'p2p_circular_loop_flag', label: 'Circular Flow' },
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

        <div className="r-reason-card">
          <div className="r-reason-label">PRIMARY REASON</div>
          <div className="r-reason-text">{result.primary_reason}</div>
        </div>

        {hasShap && (
          <div className="r-section">
            <h2 className="r-section-title">Behavioral Signal Breakdown</h2>
            <div className="r-shap-list">
              {result.shap_reasons.map((shap, idx) => (
                <div className="r-shap-row" key={idx}>
                  <div className={`r-shap-dot ${shap.direction === 'risk' ? 'dot-risk' : 'dot-strength'}`}></div>
                  <div className="r-shap-mid">
                    <div className="r-shap-reason">{shap.reason}</div>
                    <div className="r-shap-feature">{shap.feature}</div>
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
            {keyFeatures.map((kf, idx) => (
              <div className="r-feature-cell" key={idx}>
                <div className="r-f-label">{kf.label}</div>
                <div className="r-f-value">
                  {formatFeatureValue(kf.key, result.features?.[kf.key])}
                </div>
              </div>
            ))}
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
