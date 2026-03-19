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

  async function scoreUser(userId) {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.get(`http://localhost:8000/demo/${userId}`)
      setResult(res.data)
      setScreen('results')
    } catch (e) {
      setError('Failed to connect to scoring API. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {screen === 'landing' && <Landing onStart={() => setScreen('select')} />}
      {screen === 'select' && <UserSelect onScore={scoreUser} loading={loading} error={error} onBack={() => setScreen('landing')} />}
      {screen === 'results' && <Results result={result} onBack={() => setScreen('select')} />}
    </>
  )
}

export default App
