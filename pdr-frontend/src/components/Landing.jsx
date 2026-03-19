import React from 'react';
import './Landing.css';

export default function Landing({ onStart }) {
  return (
    <div className="landing-container">
      <div className="landing-content">
        <div className="landing-badge">Alternative Credit Scoring · India</div>
        <h1 className="landing-title">Credit decisions that explain themselves.</h1>
        <p className="landing-subtitle">
          PDR scores NTCs and MSMEs using behavioral signals from bank statements — no credit history required.
        </p>
        <button className="landing-btn" onClick={onStart}>
          View Demo Profiles &rarr;
        </button>
        <div className="landing-footnote">
          5 hand-crafted borrower profiles · Powered by XGBoost + SHAP
        </div>
      </div>
      <div className="landing-footer">
        PDR · Alternative Credit Intelligence
      </div>
    </div>
  );
}
