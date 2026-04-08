import React, { useEffect, useState } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import LoadingScreen from './components/LoadingScreen'
import './styles.css'

function AppBootstrap() {
  const [showLoader, setShowLoader] = useState(true)

  useEffect(() => {
    const timer = window.setTimeout(() => setShowLoader(false), 1600)
    return () => window.clearTimeout(timer)
  }, [])

  if (showLoader) {
    return <LoadingScreen />
  }

  return <App />
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AppBootstrap />
    </BrowserRouter>
  </React.StrictMode>,
)
