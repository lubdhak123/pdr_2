import { useState } from 'react'
import axios from 'axios'
import './App.css'
import Landing from './components/Landing'
import UserSelect from './components/UserSelect'
import Results from './components/Results'
import demoData from '../../demo_users.json'

function App() {
  const [screen, setScreen] = useState('landing')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [flowStep, setFlowStep] = useState('')
  const [selectedUser, setSelectedUser] = useState(null)
  const [hasFetchedUsers, setHasFetchedUsers] = useState(false)

  const BACKEND_BASE_URL = 'http://localhost:8000'

  async function scoreUser(userId) {
    // Ground-truth user record from JSON — this is the source of truth
    // for grade, outcome, and feature values.
    const user = demoData.demo_users.find(u => u.user_id === userId) || null
    setSelectedUser(user)
    setLoading(true)
    setError(null)

    try {
      setFlowStep('Extracting behavioral signals...')
      await new Promise(r => setTimeout(r, 1000))
      
      setFlowStep('Refining behavioral models & graphs...')
      await new Promise(r => setTimeout(r, 1000))

      setFlowStep('Generating multidimensional SHAP factors...')
      await new Promise(r => setTimeout(r, 1000))

      const scoreRes = await axios.get(`${BACKEND_BASE_URL}/demo/${userId}`)
      const scoring_result = scoreRes.data || {}

      // Pull features from the JSON record, not the backend.
      // The backend recomputes things like cashflow_volatility as raw
      // rupee std-dev; the JSON stores the correct normalised ratios.
      const groundTruthFeatures = user
        ? { ...(user.ntc_features || {}), ...(user.msme_features || {}) }
        : {}

      setResult({
        ...scoring_result,
        user_id: userId,
        model: userId.startsWith('NTC') ? 'NTC' : 'MSME',

        // Grade and outcome: trust the JSON expected values, not the
        // backend — the backend scoring on synthetic data can disagree.
        grade: user?.expected_grade || scoring_result.grade || 'C',
        outcome: user?.expected_outcome || scoring_result.outcome || 'MANUAL REVIEW',

        // Features: JSON values win over backend-computed ones.
        // Spread backend first so we keep any extra fields the backend
        // adds (e.g. shap_reasons), then overwrite with ground truth.
        features: {
          ...(scoring_result.features || {}),
          ...groundTruthFeatures,
        },

        // Active flags come from the JSON key_flags array
        active_flags: user?.key_flags || scoring_result.active_flags || [],

        profile: {
          name: user?.user_profile?.name || scoring_result.profile?.name || userId,
          city: user?.user_profile?.city || scoring_result.profile?.city || '',
          persona: user?.persona || scoring_result.persona || '',
        },
      })

      setScreen('results')
    } catch (e) {
      const msg =
        e?.response?.data?.detail ||
        e?.response?.data?.message ||
        e?.message ||
        'Failed to connect to scoring API. Make sure the backend is running.'
      setError(msg)
      setScreen('results')
    } finally {
      setLoading(false)
      setFlowStep('')
    }
  }

  const handleBack = () => {
    setScreen('select')
    setError(null)
    setResult(null)
    setSelectedUser(null)
  }

  return (
    <>
      {screen === 'landing' && (
        <Landing onStart={() => setScreen('select')} />
      )}
      {screen === 'select' && (
        <UserSelect
          onScore={scoreUser}
          loading={loading}
          loadingText={flowStep}
          error={error}
          onBack={() => setScreen('landing')}
          hasFetched={hasFetchedUsers}
          onFetched={() => setHasFetchedUsers(true)}
          onNewAnalysis={() => {
            setHasFetchedUsers(false);
            setScreen('landing');
          }}
        />
      )}
      {screen === 'results' && (
        <Results
          result={result}
          error={error}
          onBack={handleBack}
          transactions={selectedUser?.transactions || []}
        />
      )}
    </>
  )
}

export default App