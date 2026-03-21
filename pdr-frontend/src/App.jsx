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
      setFlowStep('Fetching demo score...')
      const scoreRes = await axios.get(`${BACKEND_BASE_URL}/demo/${userId}`)

      const scoring_result = scoreRes.data || {}

      setResult({
        ...scoring_result,
        user_id: userId,
        persona: scoring_result.persona || '',
        profile: {
          name: scoring_result.profile?.name || userId,
          city: scoring_result.profile?.city || '',
          persona: scoring_result.persona || '',
        }
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
      {screen === 'results' && <Results result={result} error={error} onBack={() => { setScreen('select'); setError(null); setResult(null); }} />}
    </>
  )
}

export default App
