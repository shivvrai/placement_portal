/**
 * Root application component — wraps AuthProvider and AppRouter.
 */

import { AuthProvider } from './context/AuthContext';
import { AppRouter } from './router/AppRouter';

export default function App() {
  return (
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  );
}
