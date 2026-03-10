import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import { debugLog, installGlobalDebugHandlers } from '@/utils/debug'
import './styles/global.css'

installGlobalDebugHandlers()
debugLog('info', 'app.bootstrap.start')

createRoot(document.getElementById('root')).render(
  <App />
)

debugLog('info', 'app.bootstrap.rendered')
