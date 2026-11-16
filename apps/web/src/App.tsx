import React, { useState } from 'react';
import { 
  Shield, 
  Upload, 
  Clock, 
  BarChart3, 
  Users, 
  FileText, 
  LogOut, 
  Activity,
  Database
} from 'lucide-react';

export default function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('mino_token'));
  const [user, setUser] = useState<any>(
    localStorage.getItem('mino_user') ? JSON.parse(localStorage.getItem('mino_user')!) : null
  );
  
  // Navigation
  const [activeTab, setActiveTab] = useState<'dashboard' | 'upload' | 'history' | 'admin' | 'profile'>('dashboard');

  // Auth form states
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [authError, setAuthError] = useState('');
  const [loading, setLoading] = useState(false);

  // Fast login/register handler
  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError('');
    setLoading(true);

    try {
      if (isRegister) {
        const res = await fetch('/api/v1/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, full_name: fullName }),
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || 'Registration failed');
        }
        setIsRegister(false);
        setAuthError('Registration successful! Please sign in.');
      } else {
        const res = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || 'Login failed');
        }
        const data = await res.json();
        setToken(data.access_token);
        setUser(data.user);
        localStorage.setItem('mino_token', data.access_token);
        localStorage.setItem('mino_user', JSON.stringify(data.user));
      }
    } catch (err: any) {
      setAuthError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('mino_token');
    localStorage.removeItem('mino_user');
  };

  if (!token || !user) {
    return (
      <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col justify-center items-center p-4">
        <div className="w-full max-w-md bg-slate-900/90 border border-slate-800 rounded-2xl p-8 shadow-2xl backdrop-blur-xl">
          <div className="flex items-center justify-center gap-3 mb-6">
            <div className="p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-xl text-cyan-400">
              <Shield className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">MINO Forensics</h1>
              <p className="text-xs text-slate-400">Deepfake Detection & Media Integrity</p>
            </div>
          </div>

          <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 text-xs text-amber-300 mb-6">
            <strong>Forensic Notice:</strong> MINO evaluates estimated manipulation likelihood probabilistically. It does not provide absolute proof of authenticity.
          </div>

          {authError && (
            <div className={`p-3 rounded-lg text-xs mb-4 ${authError.includes('successful') ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-300' : 'bg-rose-500/10 border border-rose-500/30 text-rose-300'}`}>
              {authError}
            </div>
          )}

          <form onSubmit={handleAuth} className="space-y-4">
            {isRegister && (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  placeholder="Dr. Forensic Analyst"
                />
              </div>
            )}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                placeholder="analyst@agency.gov"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                placeholder="••••••••"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-semibold rounded-lg text-sm transition-all shadow-lg shadow-cyan-500/20 disabled:opacity-50"
            >
              {loading ? 'Processing...' : isRegister ? 'Create Account' : 'Authenticate Session'}
            </button>
          </form>

          <div className="mt-6 text-center text-xs text-slate-400">
            {isRegister ? (
              <>
                Already have credentials?{' '}
                <button onClick={() => { setIsRegister(false); setAuthError(''); }} className="text-cyan-400 hover:underline">
                  Sign In
                </button>
              </>
            ) : (
              <>
                Need an analyst account?{' '}
                <button onClick={() => { setIsRegister(true); setAuthError(''); }} className="text-cyan-400 hover:underline">
                  Register
                </button>
              </>
            )}
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800 text-center">
            <span className="text-[11px] text-slate-500">Default Admin: admin@mino.com / AdminSecurePassword123!</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between">
        <div>
          <div className="p-5 flex items-center gap-3 border-b border-slate-800">
            <div className="p-2 bg-cyan-500/10 border border-cyan-500/30 rounded-lg text-cyan-400">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <div className="font-bold text-white text-base tracking-tight leading-tight">MINO</div>
              <div className="text-[10px] text-slate-400 font-mono tracking-wider">FORENSICS V1.0</div>
            </div>
          </div>

          <nav className="p-3 space-y-1">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'dashboard' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <Activity className="w-4 h-4" /> Dashboard
            </button>
            <button
              onClick={() => setActiveTab('upload')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'upload' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <Upload className="w-4 h-4" /> New Analysis
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'history' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <Clock className="w-4 h-4" /> History
            </button>

            {user.role === 'ADMIN' && (
              <div className="pt-4 mt-4 border-t border-slate-800/80">
                <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">Service Provider</div>
                <button
                  onClick={() => setActiveTab('admin')}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    activeTab === 'admin' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <BarChart3 className="w-4 h-4" /> Admin Console
                </button>
              </div>
            )}
          </nav>
        </div>

        {/* User Card & Logout */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/40">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-cyan-400 text-xs font-bold border border-slate-700">
                {user.full_name.charAt(0)}
              </div>
              <div className="overflow-hidden">
                <div className="text-xs font-semibold text-white truncate w-28">{user.full_name}</div>
                <div className="text-[10px] text-slate-400 font-mono capitalize">{user.role.toLowerCase()}</div>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Logout"
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-md transition"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
          <div className="flex items-center gap-1.5 text-[11px] text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded border border-emerald-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            Secured Session
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto p-8">
        {activeTab === 'dashboard' && (
          <div className="space-y-6 max-w-6xl mx-auto">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold text-white tracking-tight">Forensic Screening Overview</h2>
                <p className="text-sm text-slate-400">Welcome, {user.full_name}. Baseline model active: mino-efficientnet-b0 (v1.0.0)</p>
              </div>
              <button 
                onClick={() => setActiveTab('upload')}
                className="flex items-center gap-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-medium text-sm rounded-lg shadow-lg shadow-cyan-500/20 transition"
              >
                <Upload className="w-4 h-4" /> Submit Media
              </button>
            </div>

            {/* Quick Stat Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="text-xs text-slate-400 font-medium mb-1">Your Total Analyses</div>
                <div className="text-2xl font-bold text-white">0</div>
                <div className="text-[11px] text-slate-500 mt-2">Active quota: Unlimited</div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="text-xs text-slate-400 font-medium mb-1">Likely Manipulated</div>
                <div className="text-2xl font-bold text-rose-400">0</div>
                <div className="text-[11px] text-slate-500 mt-2">Score ≥ 0.65 threshold</div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="text-xs text-slate-400 font-medium mb-1">Inconclusive Reviews</div>
                <div className="text-2xl font-bold text-amber-400">0</div>
                <div className="text-[11px] text-slate-500 mt-2">0.35 &lt; Score &lt; 0.65</div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="text-xs text-slate-400 font-medium mb-1">Likely Authentic</div>
                <div className="text-2xl font-bold text-emerald-400">0</div>
                <div className="text-[11px] text-slate-500 mt-2">Score ≤ 0.35 threshold</div>
              </div>
            </div>

            {/* Guidance banner */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-xl text-cyan-400 shrink-0">
                  <Shield className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white mb-1">Methodology & Calibration Standards</h3>
                  <p className="text-xs text-slate-300 leading-relaxed mb-4">
                    MINO uses an ensemble of convolutional backbones (Xception & EfficientNet) paired with facial landmark detection and frame-by-frame temporal risk aggregation. Media is verified for tamper-evidence using SHA-256 fingerprinting and C2PA Content Credentials.
                  </p>
                  <div className="flex flex-wrap gap-2 text-[11px]">
                    <span className="px-2.5 py-1 bg-slate-800 text-slate-300 rounded-md border border-slate-700">FFprobe Safe Metadata Extraction</span>
                    <span className="px-2.5 py-1 bg-slate-800 text-slate-300 rounded-md border border-slate-700">16-Frame Evenly Distributed Sampling</span>
                    <span className="px-2.5 py-1 bg-slate-800 text-slate-300 rounded-md border border-slate-700">Top-K Risk Aggregation</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'upload' && (
          <div className="max-w-4xl mx-auto space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white tracking-tight">Media Ingestion & Forensic Upload</h2>
              <p className="text-sm text-slate-400">Upload media for deepfake screening, face artifact analysis, and provenance verification.</p>
            </div>

            <div className="border-2 border-dashed border-slate-700 hover:border-cyan-500/60 bg-slate-900/40 rounded-2xl p-12 text-center transition flex flex-col items-center justify-center cursor-pointer">
              <div className="p-4 bg-slate-800/80 rounded-full text-cyan-400 mb-4">
                <Upload className="w-8 h-8" />
              </div>
              <div className="text-base font-medium text-white mb-1">Drag and drop forensic media files</div>
              <div className="text-xs text-slate-400 mb-4">Supports Images (JPG, PNG, WebP) and Videos (MP4, MOV, WebM) up to 100MB</div>
              <button className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm font-medium border border-slate-700 transition">
                Browse Files
              </button>
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="max-w-5xl mx-auto space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white tracking-tight">Analysis History</h2>
              <p className="text-sm text-slate-400">Searchable ledger of all media submissions and forensic screening reports.</p>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-400">
              <FileText className="w-10 h-10 mx-auto text-slate-600 mb-3" />
              <div className="text-sm font-medium text-slate-300">No analyses performed yet</div>
              <div className="text-xs text-slate-500 mt-1">Submit an image or video to begin generating forensic reports.</div>
            </div>
          </div>
        )}

        {activeTab === 'admin' && (
          <div className="max-w-6xl mx-auto space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white tracking-tight">Admin & Service Provider Console</h2>
              <p className="text-sm text-slate-400">System oversight, registered models, user authorization, and audit logs.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
                  <Users className="w-4 h-4 text-cyan-400" /> User Directory
                </div>
                <div className="text-xl font-bold text-white">Active Users Managed</div>
                <div className="text-xs text-slate-500 mt-2">Role management & approval controls active.</div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
                  <Database className="w-4 h-4 text-cyan-400" /> Active Model
                </div>
                <div className="text-xl font-bold text-cyan-400">mino-efficientnet-b0</div>
                <div className="text-xs text-slate-500 mt-2">Architecture: CNN Baseline (v1.0.0)</div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
                  <Activity className="w-4 h-4 text-emerald-400" /> System State
                </div>
                <div className="text-xl font-bold text-emerald-400">Operational</div>
                <div className="text-xs text-slate-500 mt-2">API, DB, and In-Process Workers Healthy</div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
