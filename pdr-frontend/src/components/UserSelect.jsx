import React, { useState } from 'react';
import './UserSelect.css';

const DEMO_PROFILES = [
  {
    userId: 'DEMO_001',
    name: 'Rajesh Sharma',
    city: 'Bengaluru',
    personaType: 'MSME',
    persona: 'Clean IT Contractor',
    expectedGrade: 'A',
    description: 'Six months of consistent invoices, utility bills paid every month, zero bounces.',
    tags: ['Clean approval', 'Utility discipline', 'Stable income'],
  },
  {
    userId: 'DEMO_002',
    name: 'Mohammed Farouk',
    city: 'Delhi',
    personaType: 'MSME',
    persona: 'Wash Trader',
    expectedGrade: 'E',
    description: 'Circular UPI flows to same party every month. Bounce charges. GST mismatch.',
    tags: ['P2P loop detected', 'Fraud signal', 'GST fraud'],
  },
  {
    userId: 'DEMO_003',
    name: 'Sukhwinder Singh',
    city: 'Ludhiana',
    personaType: 'MSME',
    persona: 'Seasonal Farmer',
    expectedGrade: 'B',
    description: 'Two large APMC mandi payments. No income for 4 months. Zero bounces ever.',
    tags: ['Seasonal income', 'Edge case', 'Zero bounces'],
  },
  {
    userId: 'DEMO_004',
    name: 'Priya Patel',
    city: 'Surat',
    personaType: 'MSME',
    persona: 'Struggling Kirana',
    expectedGrade: 'D',
    description: 'Regular sales but five bounce charges and heavy ATM cash dependency.',
    tags: ['Bounce stress', 'Cash dependency', 'Liquidity risk'],
  },
  {
    userId: 'DEMO_005',
    name: 'Arjun Nair',
    city: 'Kochi',
    personaType: 'NTC',
    persona: 'NRI Remittance Receiver',
    expectedGrade: 'B',
    description: 'Monthly SWIFT inward remittance. No credit history. Zero bounces.',
    tags: ['No credit history', 'Alt income', 'Digital behavior'],
  },
];

export default function UserSelect({ onScore, loading, error, onBack }) {
  const [activeId, setActiveId] = useState(null);

  const handleScore = (id) => {
    setActiveId(id);
    onScore(id);
  };

  return (
    <div className="select-container">
      <button className="back-btn" onClick={onBack}>&larr; Back</button>
      <h1 className="select-title">Select a borrower profile</h1>
      <p className="select-subtitle">Each profile is designed to demonstrate a different scoring scenario</p>
      
      {error && <div className="error-banner">{error}</div>}

      <div className="cards-grid">
        {DEMO_PROFILES.map((p) => {
          const isLoading = loading && activeId === p.userId;
          const isDisabled = loading && activeId !== p.userId;
          return (
            <button 
              key={p.userId} 
              className={`profile-card ${isDisabled ? 'disabled' : ''}`}
              onClick={() => handleScore(p.userId)}
              disabled={loading}
            >
              {isLoading && <div className="loading-overlay"><div className="spinner"></div></div>}
              
              <div className="card-top-row">
                <div className={`grade-badge grade-${p.expectedGrade.toLowerCase()}`}>
                  {p.expectedGrade}
                </div>
                <div className="persona-type">{p.personaType}</div>
              </div>
              <div className="card-name-row">
                <div className="person-name">{p.name}</div>
                <div className="person-city">{p.city}</div>
              </div>
              <div className="card-description">
                {p.description}
              </div>
              <div className="card-tags">
                {p.tags.map((t, i) => <span key={i} className="card-tag">{t}</span>)}
              </div>
              <div className="card-bottom">
                Score this profile &rarr;
              </div>
            </button>
          )
        })}
      </div>
    </div>
  );
}
