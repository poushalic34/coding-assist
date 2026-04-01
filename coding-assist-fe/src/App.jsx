import "./App.css";
import { useEffect, useState } from "react";
import AuthPanel from "./components/AuthPanel";
import PracticePage from "./pages/PracticePage";
import { api, setToken } from "./lib/api";

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const me = await api.me();
        setUser(me);
      } catch {
        setToken("");
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    bootstrap();
  }, []);

  const onAuthSubmit = async ({ mode, email, password }) => {
    setLoading(true);
    setAuthError("");
    try {
      const payload = { email, password };
      const response = mode === "signup" ? await api.signup(payload) : await api.login(payload);
      setToken(response.access_token);
      setUser({ user_id: response.user_id, email: response.email });
    } catch (error) {
      setAuthError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const onLogout = () => {
    setToken("");
    setUser(null);
  };

  if (!user) {
    return <AuthPanel onSubmit={onAuthSubmit} loading={loading} error={authError} />;
  }

  return <PracticePage user={user} onLogout={onLogout} />;
}

export default App;
