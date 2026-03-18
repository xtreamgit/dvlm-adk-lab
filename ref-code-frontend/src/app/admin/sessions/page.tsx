'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-enhanced';

interface SessionData {
  session_id: string;
  username: string;
  created_at: string;
  last_activity: string;
  chat_messages: number;
  user_queries: number;
}

export default function SessionsPage() {
  const [userSessions, setUserSessions] = useState<SessionData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
    
    // Auto-refresh every 5 seconds to show new sessions
    const interval = setInterval(() => {
      loadData();
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Get all sessions
      const sessionsResponse = await apiClient.admin_getAllSessions();
      
      // API returns sessions array directly
      setUserSessions(sessionsResponse);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your sessions...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">Error Loading Sessions</div>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={loadData}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">All Sessions</h1>

        {/* Sessions Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Active Sessions</h3>
            <p className="text-3xl font-bold text-blue-600">{userSessions.length}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Total Messages</h3>
            <p className="text-3xl font-bold text-green-600">
              {userSessions.reduce((total, session) => total + (session.chat_messages || 0), 0)}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              {userSessions.reduce((total, session) => total + (session.user_queries || 0), 0)} user queries
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Most Recent Activity</h3>
            <p className="text-sm text-purple-600">
              {userSessions.length > 0 
                ? formatDate(userSessions[0]?.last_activity) 
                : 'No activity'
              }
            </p>
          </div>
        </div>

        {/* Sessions List */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">All Active Sessions</h2>
            <p className="text-gray-600">All sessions in the system</p>
          </div>
          
          {userSessions.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {userSessions.map((session, index) => (
                <div key={session.session_id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          Session {index + 1}
                        </span>
                        <span className="font-mono text-sm text-gray-600">
                          {session.session_id}
                        </span>
                      </div>
                      <div className="mt-2 flex items-center space-x-6 text-sm text-gray-500">
                        <div>
                          <span className="font-medium">Created:</span> {formatDate(session.created_at)}
                        </div>
                        <div>
                          <span className="font-medium">Last Activity:</span> {formatDate(session.last_activity)}
                        </div>
                        <div>
                          <span className="font-medium">Messages:</span> {session.chat_messages || 0}
                        </div>
                        <div>
                          <span className="font-medium">User Queries:</span> {session.user_queries || 0}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        Active
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-gray-400 text-6xl mb-4">💬</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Sessions</h3>
              <p className="text-gray-500">You don&apos;t have any active sessions yet. Start a chat to create your first session!</p>
              <Link 
                href="/"
                className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                Start Chatting
              </Link>
            </div>
          )}
        </div>

        {/* Navigation and Refresh */}
        <div className="mt-6 flex justify-between items-center">
          <a 
            href="/admin"
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            ← Back to Admin Dashboard
          </a>
          <button 
            onClick={loadData}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Refresh Sessions
          </button>
        </div>
      </div>
    </div>
  );
}
