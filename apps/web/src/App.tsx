import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Upload, 
  Clock, 
  BarChart3, 
  FileText, 
  LogOut, 
  Activity, 
  Download, 
  RotateCcw, 
  Layers 
} from 'lucide-react';

interface AnalysisJob {
  id: string;
  media_asset_id: string;
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  progress_percent: number;
  task_type: string;
  queued_at: string;
  error_message?: string;
  result?: {
    id: string;
    predicted_class: 'LIKELY_MANIPULATED' | 'INCONCLUSIVE' | 'LIKELY_AUTHENTIC';
    manipulation_score: number;
    threshold_low: number;
    threshold_high: number;
    aggregation_method: string;
    valid_frame_count: number;
    face_frame_count: number;
    result_summary: string;
    provenance_status: string;
    frame_results?: Array<{
      timestamp_ms: number;
      frame_index: number;
      manipulation_score: number;
      face_detected: boolean;
      quality_status: string;
    }>;
  };
}

export default function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('mino_token'));
  const [user, setUser] = useState<any>(
    localStorage.getItem('mino_user') ? JSON.parse(localStorage.getItem('mino_user')!) : null
  );
  
  const [activeTab, setActiveTab] = useState<'dashboard' | 'upload' | 'history' | 'admin'>('dashboard');

  // Auth states
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);

  // Analyses list & upload states
  const [analyses, setAnalyses] = useState<AnalysisJob[]>([]);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [selectedJob, setSelectedJob] = useState<AnalysisJob | null>(null);

  // Admin stats
  const [adminSummary, setAdminSummary] = useState<any>(null);

  // Load user analyses
  const fetchAnalyses = async () => {
    if (!token) return;
    try {
      const res = await fetch('/api/v1/analyses', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAnalyses(data);
        if (data.length > 0 && !selectedJob) {
          setSelectedJob(data[0]);
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Load admin summary if user is ADMIN
  const fetchAdminSummary = async () => {
    if (!token || user?.role !== 'ADMIN') return;
    try {
      const res = await fetch('/api/v1/admin/dashboard/summary', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAdminSummary(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (token) {
      fetchAnalyses();
      if (user?.role === 'ADMIN') {
        fetchAdminSummary();
      }
      const interval = setInterval(fetchAnalyses, 4000);
      return () => clearInterval(interval);
    }
  }, [token]);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError('');
    setAuthLoading(true);

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
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('mino_token');
    localStorage.removeItem('mino_user');
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !token) return;

    setUploading(true);
    setUploadError('');

    try {
      // 1. Upload media asset
      const formData = new FormData();
      formData.append('file', uploadFile);

      const mediaRes = await fetch('/api/v1/media', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });

      if (!mediaRes.ok) {
        const err = await mediaRes.json();
        throw new Error(err.detail || 'Upload rejected by forensics policy');
      }

      const mediaData = await mediaRes.json();

      // 2. Submit analysis job
      const analysisRes = await fetch('/api/v1/analyses', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ media_asset_id: mediaData.id }),
      });

      if (!analysisRes.ok) {
        const err = await analysisRes.json();
        throw new Error(err.detail || 'Failed to dispatch analysis job');
      }

      const newJob = await analysisRes.json();
      setSelectedJob(newJob);
      setUploadFile(null);
      setActiveTab('history');
      fetchAnalyses();
    } catch (err: any) {
      setUploadError(err.message || 'Error occurred during media submission');
    } finally {
      setUploading(false);
    }
  };

  const downloadPdf = (jobId: string) => {
    window.open(`/api/v1/analyses/${jobId}/report`, '_blank');
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
              disabled={authLoading}
              className="w-full py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-semibold rounded-lg text-sm transition-all shadow-lg shadow-cyan-500/20 disabled:opacity-50"
            >
              {authLoading ? 'Processing...' : isRegister ? 'Create Account' : 'Authenticate Session'}
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
              <Clock className="w-4 h-4" /> History ({analyses.length})
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

        {/* User Card */}
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

      {/* Main Workspace */}
      <main className="flex-1 overflow-y-auto p-8">
        {activeTab === 'dashboard' && (
          <div className="space-y-6 max-w-6xl mx-auto">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold text-white tracking-tight">Forensic Screening Overview</h2>
                <p className="text-sm text-slate-400">Welcome, {user.full_name}. Active Model: mino-efficientnet-b0 (v1.0.0)</p>
              </div>
              <button 
                onClick={() => setActiveTab('upload')}
                className="flex items-center gap-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-medium text-sm rounded-lg shadow-lg shadow-cyan-500/20 transition"
              >
                <Upload className="w-4 h-4" /> Submit Media
              </button>
            </div>

            {/* Metric Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="text-xs text-slate-400 font-medium mb-1">Your Total Analyses</div>
                <div className="text-2xl font-bold text-white">{analyses.length}</div>
                <div className="text-[11px] text-slate-500 mt-2">Active quota: Unlimited</div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="text-xs text-slate-400 font-medium mb-1">Likely Manipulated</div>
                <div className="text-2xl font-bold text-rose-400">
                  {analyses.filter(a => a.result?.predicted_class === 'LIKELY_MANIPULATED').length}
                </div>
                <div className="text-[11px] text-slate-500 mt-2">Score ≥ 0.65 threshold</div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="text-xs text-slate-400 font-medium mb-1">Inconclusive Reviews</div>
                <div className="text-2xl font-bold text-amber-400">
                  {analyses.filter(a => a.result?.predicted_class === 'INCONCLUSIVE').length}
                </div>
                <div className="text-[11px] text-slate-500 mt-2">0.35 &lt; Score &lt; 0.65</div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="text-xs text-slate-400 font-medium mb-1">Likely Authentic</div>
                <div className="text-2xl font-bold text-emerald-400">
                  {analyses.filter(a => a.result?.predicted_class === 'LIKELY_AUTHENTIC').length}
                </div>
                <div className="text-[11px] text-slate-500 mt-2">Score ≤ 0.35 threshold</div>
              </div>
            </div>

            {/* Educational and Standards Callout */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-xl text-cyan-400 shrink-0">
                  <Shield className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white mb-1">Methodology & Calibration Standards</h3>
                  <p className="text-xs text-slate-300 leading-relaxed mb-4">
                    MINO uses an ensemble of convolutional backbones paired with facial landmark detection and frame-by-frame temporal risk aggregation. Media is verified for tamper-evidence using SHA-256 fingerprinting and C2PA Content Credentials.
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
          <div className="max-w-3xl mx-auto space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white tracking-tight">Submit Media for Forensics</h2>
              <p className="text-sm text-slate-400">Upload high-resolution images or videos for deepfake classification and timeline scoring.</p>
            </div>

            {uploadError && (
              <div className="p-4 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl text-xs">
                {uploadError}
              </div>
            )}

            <form onSubmit={handleFileUpload} className="space-y-6">
              <div className="border-2 border-dashed border-slate-700 hover:border-cyan-500/60 bg-slate-900/40 rounded-2xl p-10 text-center transition flex flex-col items-center justify-center">
                <div className="p-4 bg-slate-800/80 rounded-full text-cyan-400 mb-4">
                  <Upload className="w-8 h-8" />
                </div>
                <div className="text-base font-medium text-white mb-1">
                  {uploadFile ? uploadFile.name : 'Choose a media file'}
                </div>
                <div className="text-xs text-slate-400 mb-6">
                  {uploadFile ? `${(uploadFile.size / (1024 * 1024)).toFixed(2)} MB` : 'Supported: JPG, PNG, WebP, MP4, MOV, WebM (Max 100MB)'}
                </div>
                <input
                  type="file"
                  id="media-file-input"
                  className="hidden"
                  accept="image/jpeg,image/png,image/webp,video/mp4,video/quicktime,video/webm"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setUploadFile(e.target.files[0]);
                    }
                  }}
                />
                <label
                  htmlFor="media-file-input"
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm font-medium border border-slate-700 transition cursor-pointer"
                >
                  Select File from Computer
                </label>
              </div>

              <button
                type="submit"
                disabled={!uploadFile || uploading}
                className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold rounded-xl text-sm transition shadow-lg shadow-cyan-500/20 disabled:opacity-40"
              >
                {uploading ? 'Analyzing Media Artifacts...' : 'Execute Deepfake Screening'}
              </button>
            </form>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="max-w-6xl mx-auto space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold text-white tracking-tight">Forensic Analysis History</h2>
                <p className="text-sm text-slate-400">Review completed evaluations, frame risk breakdowns, and forensic audit reports.</p>
              </div>
              <button 
                onClick={fetchAnalyses}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg transition"
              >
                <RotateCcw className="w-3.5 h-3.5" /> Refresh
              </button>
            </div>

            {analyses.length === 0 ? (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
                <FileText className="w-12 h-12 mx-auto text-slate-600 mb-3" />
                <div className="text-base font-medium text-slate-300">No forensic submissions yet</div>
                <div className="text-xs text-slate-500 mt-1">Submit an image or video above to generate a forensic inspection report.</div>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Analyses List */}
                <div className="space-y-3">
                  {analyses.map((job) => (
                    <div
                      key={job.id}
                      onClick={() => setSelectedJob(job)}
                      className={`p-4 rounded-xl border cursor-pointer transition ${
                        selectedJob?.id === job.id
                          ? 'bg-slate-800/80 border-cyan-500/60 shadow-lg shadow-cyan-500/10'
                          : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-mono text-slate-400">{job.id.slice(0, 8)}...</span>
                        <span className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                          job.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-400' :
                          job.status === 'PROCESSING' ? 'bg-cyan-500/10 text-cyan-400 animate-pulse' :
                          job.status === 'FAILED' ? 'bg-rose-500/10 text-rose-400' :
                          'bg-amber-500/10 text-amber-400'
                        }`}>
                          {job.status}
                        </span>
                      </div>
                      <div className="text-xs font-medium text-slate-200 truncate">
                        {job.task_type.replace(/_/g, ' ')}
                      </div>
                      {job.result && (
                        <div className="mt-2 flex items-center justify-between text-xs">
                          <span className={`font-semibold ${
                            job.result.predicted_class === 'LIKELY_MANIPULATED' ? 'text-rose-400' :
                            job.result.predicted_class === 'LIKELY_AUTHENTIC' ? 'text-emerald-400' : 'text-amber-400'
                          }`}>
                            {job.result.predicted_class.replace(/_/g, ' ')}
                          </span>
                          <span className="text-slate-400 font-mono">
                            {(job.result.manipulation_score * 100).toFixed(1)}% Risk
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Selected Result Detail View */}
                <div className="lg:col-span-2">
                  {selectedJob && (
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
                      <div className="flex items-start justify-between border-b border-slate-800 pb-4">
                        <div>
                          <div className="text-xs text-slate-400 font-mono">ANALYSIS ID: {selectedJob.id}</div>
                          <h3 className="text-lg font-bold text-white mt-1">Inspection Findings</h3>
                        </div>
                        {selectedJob.status === 'COMPLETED' && (
                          <button
                            onClick={() => downloadPdf(selectedJob.id)}
                            className="flex items-center gap-2 px-3 py-1.5 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded-lg text-xs font-semibold transition"
                          >
                            <Download className="w-3.5 h-3.5" /> Download PDF Report
                          </button>
                        )}
                      </div>

                      {selectedJob.status === 'PROCESSING' && (
                        <div className="py-8 text-center space-y-3">
                          <div className="w-10 h-10 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                          <div className="text-sm font-medium text-white">Extracting Frames & Running Neural Inference...</div>
                          <div className="w-64 h-2 bg-slate-800 rounded-full mx-auto overflow-hidden">
                            <div className="h-full bg-cyan-500 transition-all duration-300" style={{ width: `${selectedJob.progress_percent}%` }}></div>
                          </div>
                        </div>
                      )}

                      {selectedJob.result && (
                        <div className="space-y-6">
                          {/* Score and Verdict */}
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl">
                              <div className="text-[11px] text-slate-400 mb-1">Classification</div>
                              <div className={`text-base font-bold ${
                                selectedJob.result.predicted_class === 'LIKELY_MANIPULATED' ? 'text-rose-400' :
                                selectedJob.result.predicted_class === 'LIKELY_AUTHENTIC' ? 'text-emerald-400' : 'text-amber-400'
                              }`}>
                                {selectedJob.result.predicted_class.replace(/_/g, ' ')}
                              </div>
                            </div>
                            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl">
                              <div className="text-[11px] text-slate-400 mb-1">Estimated Likelihood</div>
                              <div className="text-xl font-bold font-mono text-cyan-400">
                                {(selectedJob.result.manipulation_score * 100).toFixed(1)}%
                              </div>
                            </div>
                            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl">
                              <div className="text-[11px] text-slate-400 mb-1">Sampled Face Frames</div>
                              <div className="text-base font-bold text-white">
                                {selectedJob.result.face_frame_count} / {selectedJob.result.valid_frame_count}
                              </div>
                            </div>
                          </div>

                          {/* Summary explanation */}
                          <div className="p-4 bg-slate-950/40 border border-slate-800/80 rounded-xl text-xs text-slate-300">
                            <strong>Forensic Assessment:</strong> {selectedJob.result.result_summary}
                          </div>

                          {/* Frame risk timeline if multiple frames */}
                          {selectedJob.result.frame_results && selectedJob.result.frame_results.length > 1 && (
                            <div>
                              <div className="text-xs font-semibold text-slate-300 mb-3 flex items-center gap-2">
                                <Layers className="w-4 h-4 text-cyan-400" /> Frame-by-Frame Manipulation Risk Timeline
                              </div>
                              <div className="grid grid-cols-8 gap-2">
                                {selectedJob.result.frame_results.map((fr, idx) => (
                                  <div key={idx} className="bg-slate-950 border border-slate-800 rounded-lg p-2 text-center">
                                    <div className="text-[10px] text-slate-500 font-mono">{(fr.timestamp_ms / 1000).toFixed(1)}s</div>
                                    <div className={`text-xs font-bold font-mono my-1 ${
                                      fr.manipulation_score >= 0.65 ? 'text-rose-400' :
                                      fr.manipulation_score <= 0.35 ? 'text-emerald-400' : 'text-amber-400'
                                    }`}>
                                      {(fr.manipulation_score * 100).toFixed(0)}%
                                    </div>
                                    <div className="text-[9px] text-slate-400">{fr.face_detected ? 'Face' : 'No Face'}</div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'admin' && (
          <div className="max-w-6xl mx-auto space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold text-white tracking-tight">Admin & Service Provider Console</h2>
                <p className="text-sm text-slate-400">System metrics, model activation, dataset management, and audit logs.</p>
              </div>
              <a
                href="/api/v1/admin/exports/analyses.csv"
                download
                className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold transition"
              >
                <Download className="w-3.5 h-3.5" /> Export All Analyses (CSV)
              </a>
            </div>

            {adminSummary && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                  <div className="text-xs text-slate-400 mb-1">Total Users</div>
                  <div className="text-2xl font-bold text-white">{adminSummary.total_users}</div>
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                  <div className="text-xs text-slate-400 mb-1">Total Analyses Executed</div>
                  <div className="text-2xl font-bold text-cyan-400">{adminSummary.total_analyses}</div>
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                  <div className="text-xs text-slate-400 mb-1">Active Model Version</div>
                  <div className="text-lg font-bold text-white truncate">{adminSummary.active_model.version}</div>
                  <div className="text-[10px] text-slate-400">{adminSummary.active_model.name}</div>
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                  <div className="text-xs text-slate-400 mb-1">System Health</div>
                  <div className="text-lg font-bold text-emerald-400">100% Operational</div>
                  <div className="text-[10px] text-slate-400">In-Process Worker & DB Online</div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
