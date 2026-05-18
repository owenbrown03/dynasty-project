import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router';

import './index.css'
import { App } from './App.jsx'
import { UserProvider } from './context/UserContext.tsx';

const rootElement = document.getElementById('root')!

createRoot(rootElement).render(
  <StrictMode>
    <BrowserRouter>
      <UserProvider>
        <App />
      </UserProvider>
    </BrowserRouter>
  </StrictMode>,
)