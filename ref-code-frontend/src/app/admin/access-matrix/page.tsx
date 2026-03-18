'use client';

import { useState, useEffect } from 'react';
import { Check, Info, RefreshCw } from 'lucide-react';
import { getAuthHeadersOnly } from '../../../lib/auth-headers';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || '';

interface User {
  chatbot_user_id: number;
  email: string;
  full_name: string;
  chatbot_group_name: string;
  chatbot_group_id: number;
}

interface Agent {
  id: number;
  name: string;
  display_name: string;
  description: string;
}

interface Corpus {
  id: number;
  name: string;
  display_name: string;
  description: string;
}

interface AccessMatrixData {
  users: User[];
  agents: Agent[];
  corpora: Corpus[];
  agent_assignments: Record<number, number>; // chatbot_user_id -> agent_id
  corpus_access: Record<number, number[]>; // chatbot_user_id -> corpus_ids[]
}

export default function AccessMatrixPage() {
  const [data, setData] = useState<AccessMatrixData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showInfoDialog, setShowInfoDialog] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${BACKEND_URL}/api/admin/access-matrix`, {
        headers: getAuthHeadersOnly(),
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error(`Failed to load access matrix: ${response.statusText}`);
      }
      
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load access matrix');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading access matrix...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
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

  if (!data) {
    return null;
  }

  const hasAgentAccess = (userId: number, agentId: number): boolean => {
    return data.agent_assignments[userId] === agentId;
  };

  const hasCorpusAccess = (userId: number, corpusId: number): boolean => {
    return data.corpus_access[userId]?.includes(corpusId) || false;
  };

  return (
    <div className="min-h-screen bg-gray-200 p-8">
      <div className="max-w-[1600px] mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Access Matrix</h1>
              <p className="text-gray-600 mt-1">
                View agent assignments and corpus access for all chatbot users
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowInfoDialog(true)}
                className="flex items-center gap-2 bg-gray-100 text-gray-700 px-3 py-2 rounded-lg hover:bg-gray-200"
                title="Information"
              >
                <Info className="w-5 h-5" />
              </button>
              <button
                onClick={loadData}
                className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
            </div>
          </div>
          
        </div>

        {/* Info Dialog */}
        {showInfoDialog && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowInfoDialog(false)}>
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4" onClick={(e) => e.stopPropagation()}>
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="bg-blue-100 rounded-full p-2">
                      <Info className="h-6 w-6 text-blue-600" />
                    </div>
                    <h2 className="text-xl font-semibold text-gray-900">Access Matrix Information</h2>
                  </div>
                  <button
                    onClick={() => setShowInfoDialog(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                
                <div className="space-y-4 text-gray-700">
                  <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
                    <p className="font-medium text-blue-900 mb-2">Read-Only View</p>
                    <p className="text-blue-800">
                      Access is managed through Google Workspace Groups and synced via the Google Groups Bridge.
                      To modify access, update group memberships in Google Workspace Admin Console.
                    </p>
                  </div>
                  
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">How It Works</h3>
                    <ul className="list-disc list-inside space-y-1 text-sm">
                      <li>Users are automatically synced when they log in via IAP</li>
                      <li>Group memberships are queried from Google Cloud Identity API</li>
                      <li>Agent assignments are based on chatbot group mappings</li>
                      <li>Corpus access is granted through group-to-corpus mappings</li>
                      <li>Changes sync within 5 minutes or on next login</li>
                    </ul>
                  </div>
                  
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Matrix Layout</h3>
                    <ul className="list-disc list-inside space-y-1 text-sm">
                      <li><strong>Agent Assignments:</strong> Shows which agent each user is assigned to</li>
                      <li><strong>Corpus Access:</strong> Shows which corpora each user can access</li>
                      <li>Checkmarks (✓) indicate active assignments/access</li>
                    </ul>
                  </div>
                </div>
                
                <div className="mt-6 flex justify-end">
                  <button
                    onClick={() => setShowInfoDialog(false)}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                  >
                    Got it
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Summary Stats */}
        <div className="mb-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-gray-900">{data.users.length}</div>
            <div className="text-gray-600">Active Chatbot Users</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-gray-900">{data.agents.length}</div>
            <div className="text-gray-600">Available Agents</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-gray-900">{data.corpora.length}</div>
            <div className="text-gray-600">Active Corpora</div>
          </div>
        </div>

        {/* Agent Assignments Matrix */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Agent Assignments</h2>
          <p className="text-gray-600 mb-6">
            Shows which agent each user is assigned to based on their chatbot group membership.
          </p>
          
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className="border border-gray-300 p-3 text-left font-semibold text-gray-900 sticky left-0 z-10" style={{ backgroundColor: '#cce0d8' }}>
                    User
                  </th>
                  {data.agents.map((agent) => (
                    <th
                      key={agent.id}
                      className="border border-gray-300 p-3 text-center font-medium text-gray-900 min-w-[120px]" style={{ backgroundColor: '#cce0d8' }}
                    >
                      <div className="text-sm">{agent.display_name}</div>
                      <div className="text-xs text-gray-500 mt-1">{agent.name}</div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.users.map((user, idx) => (
                  <tr key={user.chatbot_user_id} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="border border-gray-300 p-3 font-medium text-gray-900 sticky left-0 z-10" style={{ backgroundColor: idx % 2 === 0 ? '#ffffff' : '#e7e8ea' }}>
                      <div>{user.full_name || user.email}</div>
                      <div className="text-xs text-gray-500 mt-1">{user.chatbot_group_name}</div>
                    </td>
                    {data.agents.map((agent) => (
                      <td
                        key={agent.id}
                        className="border border-gray-300 p-3 text-center"
                      >
                        {hasAgentAccess(user.chatbot_user_id, agent.id) && (
                          <Check className="w-5 h-5 text-green-600 mx-auto" />
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {data.agents.length === 0 && (
            <p className="text-gray-500 text-center py-8">No agents available</p>
          )}
        </div>

        {/* Corpus Access Matrix */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Corpus Access</h2>
          <p className="text-gray-600 mb-6">
            Shows which corpora each user has access to based on their chatbot group membership.
          </p>
          
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className="border border-gray-300 p-3 text-left font-semibold text-gray-900 sticky left-0 z-10" style={{ backgroundColor: '#cce0d8' }}>
                    User
                  </th>
                  {data.corpora.map((corpus) => (
                    <th
                      key={corpus.id}
                      className="border border-gray-300 p-3 text-center font-medium text-gray-900 min-w-[120px]" style={{ backgroundColor: '#cce0d8' }}
                    >
                      <div className="text-sm">{corpus.display_name}</div>
                      <div className="text-xs text-gray-500 mt-1">{corpus.name}</div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.users.map((user, idx) => (
                  <tr key={user.chatbot_user_id} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="border border-gray-300 p-3 font-medium text-gray-900 sticky left-0 z-10" style={{ backgroundColor: idx % 2 === 0 ? '#ffffff' : '#e7e8ea' }}>
                      <div>{user.full_name || user.email}</div>
                      <div className="text-xs text-gray-500 mt-1">{user.chatbot_group_name}</div>
                    </td>
                    {data.corpora.map((corpus) => (
                      <td
                        key={corpus.id}
                        className="border border-gray-300 p-3 text-center"
                      >
                        {hasCorpusAccess(user.chatbot_user_id, corpus.id) && (
                          <Check className="w-5 h-5 text-green-600 mx-auto" />
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {data.corpora.length === 0 && (
            <p className="text-gray-500 text-center py-8">No corpora available</p>
          )}
        </div>
      </div>
    </div>
  );
}
