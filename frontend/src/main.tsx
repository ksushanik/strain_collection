// import { StrictMode } from 'react' // Временно отключен для тестирования debounce
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <App />
)
