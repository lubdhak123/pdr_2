import React, { useState } from 'react';
import './UserSelect.css';

export default function UserSelect({
  onScore,
  loading,
  loadingText,
  error,
  onBack,
}) {
  const users = [
    { user_id: 'user_001', name: 'Rajesh Sharma', city: 'Bengaluru', persona_type: 'DEMO', persona: 'Clean IT Contractor', business_type: 'Business', expected_grade: 'A' },
    { user_id: 'user_002', name: 'Mohammed Farouk', city: 'Delhi', persona_type: 'DEMO', persona: 'Wash Trader', business_type: 'Business', expected_grade: 'E' },
    { user_id: 'user_003', name: 'Sukhwinder Singh', city: 'Ludhiana', persona_type: 'DEMO', persona: 'Seasonal Farmer', business_type: 'Business', expected_grade: 'C' },
    { user_id: 'user_004', name: 'Priya Patel', city: 'Surat', persona_type: 'DEMO', persona: 'Struggling Kirana', business_type: 'Business', expected_grade: 'D' },
    { user_id: 'user_005', name: 'Arjun Nair', city: 'Kochi', persona_type: 'DEMO', persona: 'NRI Remittance Receiver', business_type: 'Business', expected_grade: 'B' }
  ];
  const [activeId, setActiveId] = useState(null);

  function handleFetchScore(userId) {
    setActiveId(userId);
    onScore(userId);
  }

  return (
    <div className="select-container">
      <button className="back-btn" onClick={onBack}>
        &larr; Back
      </button>

      <h1 className="select-title">Account Aggregator Demo</h1>
      <p className="select-subtitle">
        Select a demo user to run the PDR scoring integration.
      </p>

      {error && <div className="error-banner">{error}</div>}

      <div className="users-header">
        <div className="users-header-title">Available demo users</div>
        <div className="users-header-subtitle">
          Select one to test the backend API and see the resulting grade.
        </div>
      </div>

      <div className="cards-grid">
        {users.map((u, idx) => {
          const userId = u.user_id;
          const isLoading = loading && activeId === userId;
          const isDisabled = loading && activeId !== userId;

          return (
            <button
              key={userId}
              className={`profile-card ${isDisabled ? 'disabled' : ''}`}
              style={{ '--i': idx }}
              onClick={() => handleFetchScore(userId)}
              disabled={loading}
            >
              {isLoading && (
                <div className="loading-overlay">
                  <div className="loading-stack">
                    <div className="spinner"></div>
                    {loadingText && (
                      <div className="loading-text">{loadingText}</div>
                    )}
                  </div>
                </div>
              )}

              <div className="card-top-row">
                <div className="persona-type">
                  {u.persona_type}
                </div>
                <div className={`grade-badge grade-${u.expected_grade.toLowerCase()}`}>
                  Expect: {u.expected_grade}
                </div>
              </div>

              <div className="card-name-row">
                <div className="person-name">{u.name}</div>
                <div className="person-city">
                  {u.city}
                </div>
              </div>

              <div className="card-description">{u.persona}</div>

              <div className="card-tags">
                <span className="card-tag">
                  {u.business_type}
                </span>
                <span className="card-tag">Fetch & score</span>
              </div>

              <div className="card-bottom">Fetch & score &rarr;</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
