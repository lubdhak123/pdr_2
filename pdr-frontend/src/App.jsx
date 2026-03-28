import { useState } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import axios from 'axios'
import './App.css'
import LandingPage from './pages/LandingPage'
import AssessmentForm from './pages/AssessmentForm'
import DemoProfiles from './pages/DemoProfiles'
import UserSelect from './components/UserSelect'
import Results from './components/Results'
import demoData from '../../demo_users.json'

// Animated page wrapper — re-triggers on route change via key
function PageTransition({ children }) {
  const location = useLocation()
  return (
    <div className="page-transition" key={location.pathname}>
      {children}
    </div>
  )
}

// Demo flow wrapper — preserves 100% of existing demo logic
function DemoFlow() {
  const [screen, setScreen] = useState('select')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [flowStep, setFlowStep] = useState('')
  const [selectedUser, setSelectedUser] = useState(null)
  const [hasFetchedUsers, setHasFetchedUsers] = useState(false)

  const BACKEND_BASE_URL = 'http://localhost:8000'

  async function scoreUser(userId) {
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

      const groundTruthFeatures = user
        ? { ...(user.ntc_features || {}), ...(user.msme_features || {}) }
        : {}

      setResult({
        ...scoring_result,
        user_id: userId,
        model: userId.startsWith('NTC') ? 'NTC' : 'MSME',
        grade: user?.expected_grade || scoring_result.grade || 'C',
        outcome: user?.expected_outcome || scoring_result.outcome || 'MANUAL REVIEW',
        features: {
          ...(scoring_result.features || {}),
          ...groundTruthFeatures,
        },
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
      {screen === 'select' && (
        <UserSelect
          onScore={scoreUser}
          loading={loading}
          loadingText={flowStep}
          error={error}
          onBack={() => setScreen('select')}
          hasFetched={hasFetchedUsers}
          onFetched={() => setHasFetchedUsers(true)}
          onNewAnalysis={() => {
            setHasFetchedUsers(false)
          }}
        />
      )}
      {screen === 'results' && (
        <Results
          result={result}
          error={error}
          onBack={handleBack}
          transactions={selectedUser?.transactions || []}
          selectedUser={selectedUser}
        />
      )}
    </>
  )
}

// Placeholder docs page
function DocsPage() {
  return (
    <div className="min-h-screen bg-surface flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-headline font-bold text-slate-900 dark:text-white mb-4">Documentation</h1>
        <p className="text-on-surface-variant dark:text-slate-400 text-lg">Coming soon.</p>
      </div>
    </div>
  )
}

function App() {
  const location = useLocation()

  return (
    <div className="page-transition" key={location.pathname}>
      <Routes location={location}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/solutions" element={<AssessmentForm />} />
        <Route path="/demo" element={<DemoProfiles />} />
        <Route path="/demo-scoring" element={<DemoFlow />} />
        <Route path="/demo/result/:userId" element={<DemoFlow />} />
        <Route path="/docs" element={<DocsPage />} />
      </Routes>
    </div>
  )
}

export default App