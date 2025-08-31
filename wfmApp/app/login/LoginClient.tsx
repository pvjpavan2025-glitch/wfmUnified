'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { useAuth } from '../../contexts/auth-context'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Settings, CalendarDays, BarChart3, Eye, EyeOff, HelpCircle } from 'lucide-react'

export default function LoginClient() {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [remember, setRemember] = useState(false)
  const { login, isLoading } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!username || !password) {
      setError('Please enter username and password')
      return
    }

    const success = await login(username, password)
    if (!success) {
      setError('Invalid username or password')
    }
  }

  // Fixed animation delays to prevent hydration mismatch
  const floatDelayA = useMemo(() => 0.5, [])
  const floatDelayB = useMemo(() => 1.2, [])
  const floatDelayC = useMemo(() => 0.8, [])

  // Parallax drift (very gentle)
  const [px, setPx] = useState(0)
  const [py, setPy] = useState(0)
  const rafRef = useRef<number | null>(null)
  useEffect(() => {
    const reduceMotion = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduceMotion) return
    let targetX = 0, targetY = 0
    const onMove = (e: MouseEvent) => {
      const nx = (e.clientX / window.innerWidth - 0.5) * 2 // -1..1
      const ny = (e.clientY / window.innerHeight - 0.5) * 2
      targetX = nx
      targetY = ny
      if (rafRef.current == null) tick()
    }
    const tick = () => {
      // ease towards target
      setPx((prev) => prev + (targetX - prev) * 0.08)
      setPy((prev) => prev + (targetY - prev) * 0.08)
      rafRef.current = requestAnimationFrame(tick)
    }
    window.addEventListener('mousemove', onMove)
    return () => {
      window.removeEventListener('mousemove', onMove)
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      rafRef.current = null
    }
  }, [])

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#0B1630] text-white">
      <div className="pointer-events-none absolute inset-0">
        {/* Blob A (top-left) */}
        <div
          className="absolute -top-40 -left-40 h-[520px] w-[520px] rounded-full blur-3xl opacity-60 will-change-transform"
          style={{
            transform: `translate3d(${px * 8}px, ${py * 6}px, 0)`
          }}
        >
          <div
            className="h-full w-full rounded-full animate-rotate-a"
            style={{
              background:
                'conic-gradient(at top left, var(--wfm-navy-900), var(--wfm-navy-800), var(--wfm-navy-700), var(--wfm-navy-900))'
            }}
          />
        </div>

        {/* Blob B (bottom-right) */}
        <div
          className="absolute -bottom-32 -right-32 h-[560px] w-[560px] rounded-full blur-3xl opacity-60 will-change-transform"
          style={{
            transform: `translate3d(${px * -10}px, ${py * -8}px, 0)`
          }}
        >
          <div
            className="h-full w-full rounded-full animate-rotate-b"
            style={{
              background:
                'conic-gradient(at bottom right, var(--wfm-navy-900), var(--wfm-navy-700), var(--wfm-navy-600), var(--wfm-navy-900))'
            }}
          />
        </div>

        {/* Glow overlay */}
        <div
          className="absolute inset-0 will-change-transform"
          style={{ transform: `translate3d(${px * 4}px, ${py * 3}px, 0)` }}
        >
          <div
            className="absolute inset-0 animate-pulse-glow"
            style={{
              background:
                'radial-gradient(circle at 20% 30%, rgba(255,122,0,0.20), transparent 45%), radial-gradient(circle at 80% 70%, rgba(255,94,0,0.18), transparent 40%)'
            }}
          />
        </div>
      </div>

      <Settings className="pointer-events-none absolute left-[8%] top-[22%] h-16 w-16 text-orange-400/20 drop-shadow-[0_0_20px_rgba(255,140,0,0.2)] will-change-transform animate-float" style={{ animationDelay: `${floatDelayA}s` }} />
      <CalendarDays className="pointer-events-none absolute right-[14%] top-[38%] h-20 w-20 text-orange-300/20 drop-shadow-[0_0_20px_rgba(255,160,0,0.2)] will-change-transform animate-float-slow" style={{ animationDelay: `${floatDelayB}s` }} />
      <BarChart3 className="pointer-events-none absolute right-[10%] bottom-[10%] h-16 w-16 text-orange-200/20 drop-shadow-[0_0_20px_rgba(255,200,0,0.18)] will-change-transform animate-float" style={{ animationDelay: `${floatDelayC}s` }} />

      <div className="relative z-10 flex min-h-screen items-center justify-center px-4 py-10">
        <div className="w-full max-w-xl">
          <div className="group relative mx-auto overflow-hidden rounded-3xl border border-white/10 bg-white/5 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.6)] backdrop-blur-xl transition-transform duration-500 hover:translate-y-[-2px]">
            <div className="absolute inset-x-0 -top-24 h-32 bg-[radial-gradient(80%_120px_at_50%_100%,rgba(255,120,0,0.30),transparent)]" />

            <div className="relative px-8 pt-10 pb-6 text-center">
              <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-500 to-orange-600 shadow-[0_10px_30px_-5px_rgba(255,120,0,0.6)] ring-1 ring-white/20">
                <Settings className="h-7 w-7 text-white" />
              </div>
              <h1 className="text-2xl font-semibold tracking-[-0.02em]">Field Service Management</h1>
              <p className="mt-1 text-sm text-white/70">Admin Dashboard Login</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 px-8 pb-6">
              <div>
                <label className="mb-1 block text-sm text-white/70">Email Address</label>
                <Input
                  type="text"
                  placeholder="admin@company.com"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full rounded-xl border-white/10 bg-white/10 text-white placeholder-white/50 backdrop-blur-sm focus-visible:ring-2 focus-visible:ring-orange-400"
                  disabled={isLoading}
                />
              </div>

              <div>
                <label className="mb-1 block text-sm text-white/70">Password</label>
                <div className="relative">
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full rounded-xl border-white/10 bg-white/10 pr-10 text-white placeholder-white/50 backdrop-blur-sm focus-visible:ring-2 focus-visible:ring-orange-400"
                    disabled={isLoading}
                  />
                  <button type="button" aria-label="Toggle password visibility" onClick={() => setShowPassword((s) => !s)} className="absolute inset-y-0 right-0 inline-flex items-center pr-3 text-white/70 hover:text-white">
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between text-sm">
                <label className="inline-flex items-center gap-2 select-none">
                  <input type="checkbox" className="size-4 rounded border-white/20 bg-white/10 text-orange-500 focus:ring-orange-400" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
                  <span className="text-white/80">Remember me</span>
                </label>
              </div>

              {error && (
                <Alert className="border-red-400/40 bg-red-500/10">
                  <AlertDescription className="text-red-200">{error}</AlertDescription>
                </Alert>
              )}

              <Button
                type="submit"
                disabled={isLoading}
                className="group/button relative mt-2 w-full rounded-2xl bg-gradient-to-r from-orange-500 to-orange-600 py-3 text-base font-medium text-white shadow-[0_12px_30px_-8px_rgba(255,120,0,0.6)] transition-all duration-200 hover:from-orange-500 hover:to-orange-500 hover:shadow-[0_18px_40px_-8px_rgba(255,120,0,0.7)] disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  'Sign In'
                )}
                <span className="pointer-events-none absolute inset-0 rounded-2xl ring-1 ring-white/10" />
              </Button>

              <div className="mt-2 text-right text-sm">
                <a href="#" className="text-white/70 underline-offset-4 hover:text-white hover:underline">Forgot password?</a>
              </div>
            </form>

            <div className="grid grid-cols-3 gap-3 px-8 pb-8 pt-3 text-center text-xs text-white/80">
              <div className="rounded-xl border border-white/10 bg-white/5 py-3 backdrop-blur-sm">
                <div className="mx-auto mb-1 flex h-7 w-7 items-center justify-center rounded-lg bg-white/10"><UsersIcon /></div>
                <div>Team</div>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 py-3 backdrop-blur-sm">
                <div className="mx-auto mb-1 flex h-7 w-7 items-center justify-center rounded-lg bg-white/10"><BarChart3 className="h-4 w-4" /></div>
                <div>Analytics</div>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 py-3 backdrop-blur-sm">
                <div className="mx-auto mb-1 flex h-7 w-7 items-center justify-center rounded-lg bg-white/10"><CalendarDays className="h-4 w-4" /></div>
                <div>Schedule</div>
              </div>
            </div>
          </div>

          <p className="mt-6 text-center text-xs text-white/60">© 2024 Field Service Management. All rights reserved.</p>
        </div>

        <button className="group fixed bottom-4 right-4 inline-flex h-10 items-center justify-center gap-2 rounded-full border border-white/10 bg-white/10 px-4 text-sm text-white/90 backdrop-blur-md transition hover:bg-white/20">
          <HelpCircle className="h-4 w-4" />
          Help
        </button>
      </div>

      <style jsx global>{`
        /* Palette refined to match Figma */
        :root {
          --wfm-navy-900: #0B1630;
          --wfm-navy-800: #0E2042;
          --wfm-navy-700: #132A58;
          --wfm-navy-600: #1B3B7A;
          --wfm-orange-600: #FF5E00;
          --wfm-orange-500: #FF7A00;
          --wfm-orange-400: #FF8C1A;
        }
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-8px); }
        }
        .animate-float { animation: float 6s ease-in-out infinite; }
        .animate-float-slow { animation: float 8.5s ease-in-out infinite; }

  @keyframes rotate360a {
          0% { transform: rotate(0deg) scale(1); }
          50% { transform: rotate(180deg) scale(1.02); }
          100% { transform: rotate(360deg) scale(1); }
        }
  @keyframes rotate360b {
          0% { transform: rotate(360deg) scale(1); }
          50% { transform: rotate(180deg) scale(1.025); }
          100% { transform: rotate(0deg) scale(1); }
        }
  /* Speed up rotation (roughly 2.5x faster) */
  .animate-rotate-a { animation: rotate360a 18s linear infinite; }
  .animate-rotate-b { animation: rotate360b 24s linear infinite; }

        @keyframes pulseGlow {
          0%, 100% { opacity: 0.35; }
          50% { opacity: 0.85; }
        }
        /* Speed up glow pulse to ~6s */
        .animate-pulse-glow { animation-name: pulseGlow; animation-duration: 6s; animation-timing-function: ease-in-out; animation-iteration-count: infinite; }

        @media (prefers-reduced-motion: reduce) {
          .animate-float, .animate-float-slow, .animate-rotate-a, .animate-rotate-b, .animate-pulse-glow { animation: none !important; }
        }
      `}</style>
    </div>
  )
}

function UsersIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
      <path d="M16 11c1.657 0 3-1.79 3-4s-1.343-4-3-4-3 1.79-3 4 1.343 4 3 4Zm-8 0c1.657 0 3-1.79 3-4S9.657 3 8 3 5 4.79 5 7s1.343 4 3 4Zm0 2c-2.33 0-7 1.17-7 3.5V19a2 2 0 0 0 2 2h10.05a5.99 5.99 0 0 1-.05-.75c0-1.81.79-3.43 2.04-4.55C13.59 14.51 10.66 13 8 13Zm8 1c-3.314 0-6 1.79-6 4v.25c0 .414.336.75.75.75h10.5c.414 0 .75-.336.75-.75V18c0-2.21-2.686-4-6-4Z" />
    </svg>
  )
}
