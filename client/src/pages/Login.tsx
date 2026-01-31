import { Component, createSignal, Show } from 'solid-js';
import { useNavigate } from '@solidjs/router';
import { useAuth } from '../context/AuthContext';

const Login: Component = () => {
  const [email, setEmail] = createSignal('');
  const [password, setPassword] = createSignal('');
  const [error, setError] = createSignal('');
  const [isLoading, setIsLoading] = createSignal(false);
  
  const auth = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await auth.login({ email: email(), password: password() });
      navigate('/');
    } catch (err: any) {
      setError(err.error || 'Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-slate-900 dark:to-slate-800 p-4">
      <div class="w-full max-w-md">
        <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl p-8 border border-slate-200 dark:border-slate-700">
          {/* Logo/Title */}
          <div class="text-center mb-8">
            <h1 class="text-3xl font-bold text-slate-900 dark:text-white mb-2">Bio-Radar</h1>
            <p class="text-slate-600 dark:text-slate-400">Agricultural Intelligence Platform</p>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} class="space-y-6">
            <Show when={error()}>
              <div class="bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800 rounded-lg p-4">
                <p class="text-sm text-rose-600 dark:text-rose-400">{error()}</p>
              </div>
            </Show>

            <div>
              <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                Email
              </label>
              <input
                type="email"
                value={email()}
                onInput={(e) => setEmail(e.currentTarget.value)}
                required
                placeholder="your@email.com"
                class="w-full px-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
              />
            </div>

            <div>
              <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                Password
              </label>
              <input
                type="password"
                value={password()}
                onInput={(e) => setPassword(e.currentTarget.value)}
                required
                placeholder="••••••••"
                class="w-full px-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading()}
              class="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-bold rounded-xl transition-all shadow-lg shadow-blue-500/30 active:scale-95 disabled:cursor-not-allowed"
            >
              {isLoading() ? 'Logging in...' : 'Login'}
            </button>
          </form>

          {/* Demo Credentials */}
          <div class="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <p class="text-xs font-bold text-blue-900 dark:text-blue-300 mb-2">Demo Credentials:</p>
            <p class="text-xs text-blue-700 dark:text-blue-400">Email: test@bioradar.com</p>
            <p class="text-xs text-blue-700 dark:text-blue-400">Password: test123456</p>
          </div>

          {/* Register Link */}
          <div class="mt-6 text-center">
            <p class="text-sm text-slate-600 dark:text-slate-400">
              Don't have an account?{' '}
              <a href="/register" class="text-blue-600 hover:text-blue-700 font-semibold">
                Register here
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
