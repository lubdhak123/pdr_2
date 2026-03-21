import { useState } from 'react'
import axios from 'axios'
import './App.css'
import Landing from './components/Landing'
import UserSelect from './components/UserSelect'
import Results from './components/Results'

function App() {
  const [screen, setScreen] = useState('landing')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [flowStep, setFlowStep] = useState('')

  const BACKEND_BASE_URL = 'http://localhost:8000'

  async function scoreUser(userId) {
    setLoading(true)
    setError(null)
    try {
      // Simulated AA flow:
      // 1) Create consent
      // 2) Fetch profile + statements
      // 3) Run full AA-integrated scoring (returns SHAP reasons)
      setFlowStep('Requesting consent...')
      const consentRes = await axios.post(
        `${BACKEND_BASE_URL}/aa/users/${userId}/consent`
      )
      const consent_id = consentRes.data.consent_id

      setFlowStep('Fetching profile...')
      const profileRes = await axios.get(
        `${BACKEND_BASE_URL}/aa/users/${userId}/profile`
      )
      const aaProfile = profileRes.data?.profile || {}

      setFlowStep('Fetching statements...')
      await axios.get(`${BACKEND_BASE_URL}/aa/users/${userId}/statements`)

      setFlowStep('Running AA score...')
      const scoreRes = await axios.post(`${BACKEND_BASE_URL}/aa/score`, {
        user_id: userId,
        consent_id,
      })

      const wrapped = scoreRes.data || {}
      const scoring_result = wrapped.scoring_result || wrapped

      // Results page expects the plain scoring_result shape, so we merge identifiers from the AA wrapper.
      setResult({
        ...scoring_result,
        user_id: wrapped.user_id ?? userId,
        persona: wrapped.persona,
        profile: {
          name: aaProfile?.name,
          city: aaProfile?.city,
          persona: wrapped.persona,
        },
        consent_id: wrapped.consent_id,
        account_summary: wrapped.account_summary,
        aa_version: wrapped.aa_version,
        message: wrapped.message,
      })
      setScreen('results')
    } catch (e) {
      const msg =
        e?.response?.data?.detail ||
        e?.response?.data?.message ||
        e?.message ||
        'Failed to connect to scoring API. Make sure the backend is running.'
      setError(msg)
    } finally {
      setLoading(false)
      setFlowStep('')
    }
  }

  return (
    <>
      {screen === 'landing' && <Landing onStart={() => setScreen('select')} />}
      {screen === 'select' && (
        <UserSelect
          onScore={scoreUser}
          loading={loading}
          loadingText={flowStep}
          error={error}
          onBack={() => setScreen('landing')}
        />
      )}
      {screen === 'results' && <Results result={result} onBack={() => setScreen('select')} />}
    </>
  )
}

export default App
