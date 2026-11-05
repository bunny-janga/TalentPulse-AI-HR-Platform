import { useState } from 'react';
import { ErrorBoundary } from '../components/ui/ErrorBoundary.jsx';
import { ToastProvider } from '../components/ui/Toast.jsx';
import LandingPage from '../features/landing/LandingPage.jsx';
import LoginPage from '../features/auth/LoginPage.jsx';
import { Shell } from './Shell.jsx';
import { AppProvider, useApp } from './store.jsx';

/** Signed-out visitors see the Project Overview / Landing page, with Sign In on the top menu bar. */
function Root() {
  const { session } = useApp();
  const [showLogin, setShowLogin] = useState(false);

  if (session) {
    return <Shell />;
  }

  if (showLogin) {
    return <LoginPage onBack={() => setShowLogin(false)} />;
  }

  return <LandingPage onSignIn={() => setShowLogin(true)} />;
}

export default function App() {
  return (
    <ToastProvider>
      <AppProvider>
        <ErrorBoundary>
          <Root />
        </ErrorBoundary>
      </AppProvider>
    </ToastProvider>
  );
}
