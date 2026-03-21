import React, { useState } from 'react';
import axios from 'axios';
import './UserSelect.css';

const BACKEND_BASE_URL = 'http://localhost:8000';

export default function UserSelect({
  onScore,
  loading,
  loadingText,
  error,
  onBack,
}) {
  const [stage, setStage] = useState('idle'); // idle | list
  const [users, setUsers] = useState([]);
  const [fetchingUsers, setFetchingUsers] = useState(false);
  const [fetchError, setFetchError] = useState(null);
  const [activeId, setActiveId] = useState(null);
  const [fetchPhase, setFetchPhase] = useState('idle'); // idle | fetching | success

  async function fetchUsers() {
    setFetchError(null);
    setFetchingUsers(true);
    setFetchPhase('fetching');
    try {
      const res = await axios.get(`${BACKEND_BASE_URL}/aa/users`);
      const list = res.data?.users || [];
      setUsers(list);
      // Wait 4 seconds before showing success (keep fetching state for 4 seconds minimum)
      setTimeout(() => {
        setFetchPhase('success');
        // Show success for 1.5 seconds before moving to list
        setTimeout(() => {
          setStage('list');
          setFetchPhase('idle');
          setFetchingUsers(false);
        }, 1500);
      }, 4000);
    } catch (e) {
      const msg =
        e?.response?.data?.detail ||
        e?.response?.data?.message ||
        e?.message ||
        'Failed to fetch available users from backend.';
      setFetchError(msg);
      setFetchPhase('idle');
      setFetchingUsers(false);
    }
  }

  function handleFetchScore(userId) {
    setActiveId(userId);
    onScore(userId);
  }

  const mergedError = error || fetchError;

  return (
    <div className="select-container">
      <button className="back-btn" onClick={onBack}>
        &larr; Back
      </button>

      <h1 className="select-title">Account Aggregator Demo</h1>
      <p className="select-subtitle">
        Fetch available users, then consent + fetch data + score (AA flow).
      </p>

      {mergedError && <div className="error-banner">{mergedError}</div>}

      {(fetchPhase === 'fetching' || fetchPhase === 'success') && (
        <div className="fetch-modal-overlay">
          <div className="fetch-modal">
            {fetchPhase === 'fetching' && (
              <>
                <div className="fetch-spinner"></div>
                <div className="fetch-status-text">Fetching users...</div>
                <div className="fetch-status-subtext">Connecting to backend</div>
              </>
            )}
            {fetchPhase === 'success' && (
              <>
                <div className="fetch-success-icon">✓</div>
                <div className="fetch-status-text">Users fetched!</div>
                <div className="fetch-status-subtext">
                  {users?.length || 0} users ready
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {mergedError && <div className="error-banner">{mergedError}</div>}

      {stage === 'idle' && (
        <div className="fetch-users-block">
          <button
            className="fetch-users-btn"
            onClick={fetchUsers}
            disabled={fetchingUsers}
          >
            {fetchingUsers ? 'Fetching users...' : 'Fetch users'}
          </button>
          <div className="fetch-users-subtext">
            This calls <code>GET /aa/users</code> from the backend.
          </div>
        </div>
      )}

      {stage === 'list' && (
        <>
          <div className="users-header">
            <div className="users-header-title">Available users</div>
            <div className="users-header-subtitle">
              Select one to run the full AA-integrated scoring flow.
            </div>
          </div>

          <div className="cards-grid">
            {users.map((u, idx) => {
              const userId = u?.user_id;
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
                      {u?.persona_type || 'AA USER'}
                    </div>
                  </div>

                  <div className="card-name-row">
                    <div className="person-name">{u?.name || userId}</div>
                    <div className="person-city">
                      {u?.city || 'Unknown'}
                    </div>
                  </div>

                  <div className="card-description">{u?.persona || ''}</div>

                  <div className="card-tags">
                    <span className="card-tag">
                      {u?.business_type || 'Business'}
                    </span>
                    <span className="card-tag">Fetch & score</span>
                  </div>

                  <div className="card-bottom">Fetch & score &rarr;</div>
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
