'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { apiClient } from '@/lib/api-enhanced';
import { AnimatedCounter, PulseDot, PageTransition, FadeIn, HoverCard, Shimmer } from '@/components/motion/AnimatedComponents';

const BRAND = '#005440';
const AUTO_REFRESH_SECONDS = 30;

interface SessionEntry {
  session_id: string;
  user_id: number;
  username: string;
  email: string;
  full_name: string;
  created_at: string;
  last_activity: string;
  seconds_ago: number;
  duration_seconds: number;
  agent_name: string;
  agent_key: string;
  active_corpora: string[];
  message_count: number;
  user_query_count: number;
  session_count: number;
}

interface Summary {
  users_5m: number;
  users_10m: number;
  users_30m: number;
  users_60m: number;
  total_active_sessions: number;
  total_users_with_sessions: number;
  total_registered_users: number;
  sessions_created_today: number;
  total_messages: number;
  total_queries: number;
}

interface BoardData {
  sessions: SessionEntry[];
  summary: Summary;
  server_time: string;
}

type TimeFilter = '5m' | '10m' | '30m' | '60m' | 'all';

function formatRelativeTime(seconds: number): string {
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}h ${m}m`;
}

function getStatusColor(secondsAgo: number): string {
  if (secondsAgo <= 300) return 'bg-green-500';
  if (secondsAgo <= 1800) return 'bg-yellow-400';
  return 'bg-gray-300';
}

function getStatusLabel(secondsAgo: number): string {
  if (secondsAgo <= 300) return 'Active';
  if (secondsAgo <= 1800) return 'Recent';
  return 'Idle';
}

function filterByTime(sessions: SessionEntry[], filter: TimeFilter): SessionEntry[] {
  if (filter === 'all') return sessions;
  const thresholds: Record<string, number> = { '5m': 300, '10m': 600, '30m': 1800, '60m': 3600 };
  const max = thresholds[filter];
  return sessions.filter(s => s.seconds_ago <= max);
}

export default function AdminPage() {
  const [data, setData] = useState<BoardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeFilter, setTimeFilter] = useState<TimeFilter>('all');
  const [countdown, setCountdown] = useState(AUTO_REFRESH_SECONDS);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const countdownRef = useRef(AUTO_REFRESH_SECONDS);

  const loadData = useCallback(async (showSpinner = false) => {
    try {
      if (showSpinner) setLoading(true);
      setError(null);
      const result = await apiClient.admin_getActiveSessionBoard();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
      countdownRef.current = AUTO_REFRESH_SECONDS;
      setCountdown(AUTO_REFRESH_SECONDS);
    }
  }, []);

  useEffect(() => {
    loadData(true);
  }, [loadData]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      countdownRef.current -= 1;
      setCountdown(countdownRef.current);
      if (countdownRef.current <= 0) {
        loadData(false);
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [autoRefresh, loadData]);

  const summary = data?.summary;
  const sessions = data?.sessions || [];
  const filtered = filterByTime(sessions, timeFilter);

  const timeFilters: { key: TimeFilter; label: string }[] = [
    { key: '5m', label: '5 min' },
    { key: '10m', label: '10 min' },
    { key: '30m', label: '30 min' },
    { key: '60m', label: '1 hour' },
    { key: 'all', label: 'All' },
  ];

  // Chart data derived from summary
  const chartData = summary ? [
    { name: '5m', users: summary.users_5m, color: '#22c55e' },
    { name: '10m', users: summary.users_10m, color: '#84cc16' },
    { name: '30m', users: summary.users_30m, color: '#eab308' },
    { name: '1h', users: summary.users_60m, color: '#f97316' },
  ] : [];

  if (loading && !data) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="mb-6">
            <Shimmer className="h-8 w-64 mb-2" />
            <Shimmer className="h-4 w-40" />
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="bg-white rounded-xl border p-4">
                <Shimmer className="h-3 w-20 mb-3" />
                <Shimmer className="h-8 w-16 mb-2" />
                <Shimmer className="h-1 w-full" />
              </div>
            ))}
          </div>
          <div className="bg-white rounded-xl border p-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex gap-4 py-3">
                <Shimmer className="h-4 w-16" />
                <Shimmer className="h-4 w-32" />
                <Shimmer className="h-4 w-20" />
                <Shimmer className="h-4 w-20" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <FadeIn direction="up">
          <div className="text-center bg-white rounded-2xl shadow-lg p-10 border">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-50 flex items-center justify-center">
              <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" /></svg>
            </div>
            <div className="text-red-600 text-xl font-semibold mb-2">Error Loading Session Board</div>
            <p className="text-gray-500 mb-6">{error}</p>
            <button onClick={() => loadData(true)} className="text-white px-6 py-2.5 rounded-lg hover:opacity-90 transition-opacity font-medium" style={{ backgroundColor: BRAND }}>
              Retry
            </button>
          </div>
        </FadeIn>
      </div>
    );
  }

  return (
    <PageTransition className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <FadeIn direction="down" duration={0.4}>
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Active Session Board</h1>
              <p className="text-sm text-gray-500 mt-1">Real-time usage overview</p>
            </div>
            <div className="flex items-center gap-3">
              <AnimatePresence>
                {error && (
                  <motion.span
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 10 }}
                    className="text-xs text-red-500 bg-red-50 px-2 py-1 rounded-full"
                  >
                    Refresh failed
                  </motion.span>
                )}
              </AnimatePresence>
              <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="rounded"
                />
                Auto-refresh
              </label>
              {autoRefresh && (
                <div className="relative w-8 h-8">
                  <svg className="w-8 h-8 -rotate-90" viewBox="0 0 32 32">
                    <circle cx="16" cy="16" r="14" fill="none" stroke="#e5e7eb" strokeWidth="2" />
                    <motion.circle
                      cx="16" cy="16" r="14" fill="none" stroke={BRAND} strokeWidth="2"
                      strokeDasharray={88}
                      strokeDashoffset={88 - (88 * countdown) / AUTO_REFRESH_SECONDS}
                      strokeLinecap="round"
                      transition={{ duration: 0.3 }}
                    />
                  </svg>
                  <span className="absolute inset-0 flex items-center justify-center text-[10px] font-medium text-gray-500 tabular-nums">{countdown}</span>
                </div>
              )}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => loadData(false)}
                className="text-white px-4 py-2 rounded-lg text-sm font-medium hover:opacity-90 transition-opacity shadow-sm"
                style={{ backgroundColor: BRAND }}
              >
                Refresh
              </motion.button>
            </div>
          </div>
        </FadeIn>

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-7 gap-4 mb-8">
            {/* Active Users Cards */}
            {[
              { label: 'Active (5m)', value: summary.users_5m, color: '#22c55e', bgColor: 'bg-green-50', barColor: 'bg-green-500' },
              { label: 'Active (30m)', value: summary.users_30m, color: '#eab308', bgColor: 'bg-yellow-50', barColor: 'bg-yellow-400' },
              { label: 'Active (1h)', value: summary.users_60m, color: '#f97316', bgColor: 'bg-orange-50', barColor: 'bg-orange-400' },
            ].map((card, i) => (
              <HoverCard key={card.label} className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 cursor-default">
                <FadeIn delay={i * 0.08} direction="up">
                  <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">{card.label}</div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <AnimatedCounter value={card.value} className="text-2xl font-bold" style={{ color: BRAND }} />
                    <span className="text-xs text-gray-400">users</span>
                  </div>
                  <div className="mt-2 h-1.5 rounded-full bg-gray-100 overflow-hidden">
                    <motion.div
                      className={`h-1.5 rounded-full ${card.barColor}`}
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.min(100, summary.total_registered_users > 0 ? (card.value / summary.total_registered_users) * 100 : 0)}%` }}
                      transition={{ duration: 0.8, delay: 0.3 + i * 0.1, ease: 'easeOut' }}
                    />
                  </div>
                </FadeIn>
              </HoverCard>
            ))}

            {/* Sessions Card */}
            <HoverCard className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 cursor-default">
              <FadeIn delay={0.24} direction="up">
                <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">Sessions (2h)</div>
                <div className="mt-2 flex items-baseline gap-2">
                  <AnimatedCounter value={summary.total_active_sessions} className="text-2xl font-bold text-blue-600" />
                  <span className="text-xs text-gray-400">recent</span>
                </div>
                <div className="text-xs text-gray-400 mt-2">{summary.sessions_created_today} new today</div>
              </FadeIn>
            </HoverCard>

            {/* Messages Card */}
            <HoverCard className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 cursor-default">
              <FadeIn delay={0.32} direction="up">
                <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">Messages</div>
                <div className="mt-2 flex items-baseline gap-2">
                  <AnimatedCounter value={summary.total_messages} className="text-2xl font-bold text-purple-600" />
                  <span className="text-xs text-gray-400">total</span>
                </div>
                <div className="text-xs text-gray-400 mt-2">{summary.total_queries} queries</div>
              </FadeIn>
            </HoverCard>

            {/* Registered Card */}
            <HoverCard className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 cursor-default">
              <FadeIn delay={0.4} direction="up">
                <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">Registered</div>
                <div className="mt-2 flex items-baseline gap-2">
                  <AnimatedCounter value={summary.total_registered_users} className="text-2xl font-bold text-gray-700" />
                  <span className="text-xs text-gray-400">users</span>
                </div>
                <div className="text-xs text-gray-400 mt-2">{summary.total_users_with_sessions} with sessions</div>
              </FadeIn>
            </HoverCard>

            {/* Mini Bar Chart Card */}
            <HoverCard className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 cursor-default">
              <FadeIn delay={0.48} direction="up">
                <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Activity</div>
                <div className="h-16">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} barCategoryGap="20%">
                      <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
                      <YAxis hide />
                      <Tooltip
                        contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #e5e7eb', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
                        formatter={(value: number | string | undefined) => [`${value ?? 0} users`, 'Active']}
                      />
                      <Bar dataKey="users" radius={[3, 3, 0, 0]} animationDuration={800}>
                        {chartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </FadeIn>
            </HoverCard>
          </div>
        )}

        {/* Time Filter Tabs */}
        <FadeIn delay={0.3} direction="up">
          <div className="flex items-center gap-1.5 mb-4">
            <span className="text-sm text-gray-500 mr-2">Show:</span>
            {timeFilters.map(f => (
              <motion.button
                key={f.key}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setTimeFilter(f.key)}
                className={`relative px-3.5 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  timeFilter === f.key
                    ? 'text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
                style={timeFilter === f.key ? { backgroundColor: BRAND } : undefined}
              >
                {timeFilter === f.key && (
                  <motion.div
                    layoutId="activeFilter"
                    className="absolute inset-0 rounded-full"
                    style={{ backgroundColor: BRAND }}
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}
                <span className="relative z-10">{f.label}</span>
              </motion.button>
            ))}
            <span className="ml-auto text-sm text-gray-400">
              <AnimatePresence mode="wait">
                <motion.span
                  key={filtered.length}
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 8 }}
                  transition={{ duration: 0.2 }}
                >
                  {filtered.length} session{filtered.length !== 1 ? 's' : ''}
                </motion.span>
              </AnimatePresence>
            </span>
          </div>
        </FadeIn>

        {/* Sessions Table */}
        <FadeIn delay={0.4} direction="up">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50/80">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Activity</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Msgs</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Queries</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Agent</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Corpora</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  <AnimatePresence mode="popLayout">
                    {filtered.map((session, index) => (
                      <motion.tr
                        key={session.session_id}
                        initial={{ opacity: 0, x: -12 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 12 }}
                        transition={{ duration: 0.25, delay: index * 0.03 }}
                        className="hover:bg-gray-50/80 transition-colors"
                      >
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            <PulseDot
                              color={getStatusColor(session.seconds_ago)}
                              active={session.seconds_ago <= 300}
                            />
                            <span className="text-xs text-gray-500">{getStatusLabel(session.seconds_ago)}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-gray-900">{session.full_name || session.username}</span>
                            {session.session_count > 1 && (
                              <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded-full">{session.session_count} sessions</span>
                            )}
                          </div>
                          <div className="text-xs text-gray-400">{session.email}</div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className={`text-sm ${session.seconds_ago <= 300 ? 'font-medium' : ''}`} style={session.seconds_ago <= 300 ? { color: BRAND } : { color: '#6b7280' }}>
                            {formatRelativeTime(session.seconds_ago)}
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                          {formatDuration(session.duration_seconds)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-right font-medium text-gray-700">
                          {session.message_count}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-right font-medium text-gray-700">
                          {session.user_query_count}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-100">
                            {session.agent_name}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-1">
                            {Array.isArray(session.active_corpora) && session.active_corpora.length > 0 ? (
                              session.active_corpora.map((c, i) => (
                                <span key={i} className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-50 text-gray-600 border border-gray-200">
                                  {typeof c === 'string' ? c : String(c)}
                                </span>
                              ))
                            ) : (
                              <span className="text-xs text-gray-300">-</span>
                            )}
                          </div>
                        </td>
                      </motion.tr>
                    ))}
                  </AnimatePresence>
                </tbody>
              </table>
            </div>

            <AnimatePresence>
              {filtered.length === 0 && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="text-center py-16"
                >
                  <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-gray-100 flex items-center justify-center">
                    <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" /></svg>
                  </div>
                  <p className="text-gray-400 text-sm">
                    {sessions.length === 0
                      ? 'No active sessions'
                      : `No sessions in the last ${timeFilter === '5m' ? '5 minutes' : timeFilter === '10m' ? '10 minutes' : timeFilter === '30m' ? '30 minutes' : '1 hour'}`}
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </FadeIn>
      </div>
    </PageTransition>
  );
}
