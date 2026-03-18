'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-enhanced';

const BRAND_GREEN = 'rgb(0,84,64)';

interface AgentInfo {
  id: number;
  name: string;
  display_name: string;
  config_path: string;
  description?: string;
  agent_type?: string;
  tools?: string[];
}

interface UserAssignment {
  id: number;
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
  default_agent: AgentInfo | null;
  accessible_agents: AgentInfo[];
}

const AGENT_COLORS: Record<string, { bg: string; text: string; border: string; badge: string }> = {
  agent1: { bg: 'bg-blue-50', text: 'text-blue-800', border: 'border-blue-200', badge: 'bg-blue-600' },
  agent2: { bg: 'bg-emerald-50', text: 'text-emerald-800', border: 'border-emerald-200', badge: 'bg-emerald-600' },
  agent3: { bg: 'bg-amber-50', text: 'text-amber-800', border: 'border-amber-200', badge: 'bg-amber-600' },
  default_agent: { bg: 'bg-purple-50', text: 'text-purple-800', border: 'border-purple-200', badge: 'bg-purple-600' },
};

function getAgentColor(agentName: string) {
  return AGENT_COLORS[agentName] || AGENT_COLORS['default_agent'];
}

export default function AgentAssignmentsPage() {
  const [users, setUsers] = useState<UserAssignment[]>([]);
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState<number | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState<UserAssignment | null>(null);
  const [showAccessDialog, setShowAccessDialog] = useState(false);
  const [showAgentDetail, setShowAgentDetail] = useState<AgentInfo | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [assignmentsData, agentsData] = await Promise.all([
        apiClient.admin_getAgentAssignments(),
        apiClient.admin_getAgentsList(),
      ]);
      setUsers(assignmentsData);
      setAgents(agentsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const refreshData = async () => {
    try {
      const [assignmentsData, agentsData] = await Promise.all([
        apiClient.admin_getAgentAssignments(),
        apiClient.admin_getAgentsList(),
      ]);
      setUsers(assignmentsData);
      setAgents(agentsData);
      if (selectedUser) {
        const updated = assignmentsData.find((u: UserAssignment) => u.id === selectedUser.id);
        if (updated) setSelectedUser(updated);
      }
    } catch (err) {
      console.error('Failed to refresh:', err);
    }
  };

  const handleSetDefaultAgent = async (userId: number, agentId: number) => {
    try {
      setSaving(userId);
      setSuccessMsg(null);
      await apiClient.admin_setUserDefaultAgent(userId, agentId);
      await refreshData();
      const user = users.find(u => u.id === userId);
      const agent = agents.find(a => a.id === agentId);
      setSuccessMsg(`${user?.username}'s agent set to ${agent?.display_name}`);
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to set agent');
    } finally {
      setSaving(null);
    }
  };

  const handleGrantAccess = async (userId: number, agentId: number) => {
    try {
      await apiClient.admin_grantAgentAccess(userId, agentId);
      await refreshData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to grant access');
    }
  };

  const handleRevokeAccess = async (userId: number, agentId: number) => {
    const user = users.find(u => u.id === userId);
    if (!confirm(`Revoke ${user?.username}'s access to this agent?`)) return;
    try {
      await apiClient.admin_revokeAgentAccess(userId, agentId);
      await refreshData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to revoke access');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2" style={{ borderColor: BRAND_GREEN }}></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 text-lg mb-4">{error}</p>
          <button onClick={loadData} className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300">Retry</button>
        </div>
      </div>
    );
  }

  const assignableAgents = agents;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">User Agent Assignments</h1>
          <p className="text-gray-600">Assign agents to users and manage their access levels</p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Success Message */}
      {successMsg && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-800 text-sm flex items-center gap-2">
          <span>&#10003;</span>
          {successMsg}
        </div>
      )}

      {/* Agent Legend */}
      <div className="mb-6 p-4 bg-white rounded-lg shadow-sm border border-gray-200">
        <h3 className="text-sm font-semibold text-gray-700 uppercase mb-3">Available Agents</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {assignableAgents.map(agent => {
            const colors = getAgentColor(agent.name);
            return (
              <button
                key={agent.id}
                onClick={() => setShowAgentDetail(showAgentDetail?.id === agent.id ? null : agent)}
                className={`p-3 rounded-lg border-2 ${colors.bg} ${colors.border} text-left transition-all hover:shadow-md`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span className={`font-semibold ${colors.text}`}>{agent.display_name}</span>
                    <p className="text-xs text-gray-600 mt-1">{agent.description || agent.config_path}</p>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-xs text-white ${colors.badge}`}>
                    {agent.tools?.length || 0} tools
                  </span>
                </div>
                {showAgentDetail?.id === agent.id && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <p className="text-xs font-medium text-gray-600 mb-1">Tools:</p>
                    <div className="flex flex-wrap gap-1">
                      {agent.tools?.map(tool => (
                        <span key={tool} className="px-2 py-0.5 rounded text-xs bg-white border border-gray-300 text-gray-700">
                          {tool}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Current Agent</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Change Agent</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Additional Access</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {users.map(user => {
              const defaultAgent = user.default_agent;
              const colors = defaultAgent ? getAgentColor(defaultAgent.name) : null;
              const isSaving = saving === user.id;

              return (
                <tr key={user.id} className="hover:bg-gray-50">
                  {/* User Info */}
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">{user.username}</div>
                    <div className="text-xs text-gray-500">{user.email}</div>
                    {user.full_name && <div className="text-xs text-gray-400">{user.full_name}</div>}
                  </td>

                  {/* Current Agent Badge */}
                  <td className="px-6 py-4">
                    {defaultAgent ? (
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${colors?.bg} ${colors?.text} border ${colors?.border}`}>
                        {defaultAgent.display_name}
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-50 text-red-700 border border-red-200">
                        Not Assigned
                      </span>
                    )}
                  </td>

                  {/* Agent Dropdown */}
                  <td className="px-6 py-4">
                    <div className="relative">
                      <select
                        value={defaultAgent?.id || ''}
                        onChange={(e) => {
                          const agentId = parseInt(e.target.value);
                          if (agentId && agentId !== defaultAgent?.id) {
                            handleSetDefaultAgent(user.id, agentId);
                          }
                        }}
                        disabled={isSaving}
                        className="block w-full pl-3 pr-8 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:border-transparent bg-white disabled:opacity-50 disabled:cursor-wait"
                        style={{ focusRingColor: BRAND_GREEN } as React.CSSProperties}
                      >
                        <option value="">-- Select Agent --</option>
                        {assignableAgents.map(agent => (
                          <option key={agent.id} value={agent.id}>
                            {agent.display_name}
                          </option>
                        ))}
                      </select>
                      {isSaving && (
                        <div className="absolute right-8 top-1/2 -translate-y-1/2">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2" style={{ borderColor: BRAND_GREEN }}></div>
                        </div>
                      )}
                    </div>
                  </td>

                  {/* Additional Access */}
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {user.accessible_agents
                        .filter(a => a.id !== defaultAgent?.id)
                        .map(agent => {
                          const ac = getAgentColor(agent.name);
                          return (
                            <span key={agent.id} className={`inline-flex items-center px-2 py-0.5 rounded text-xs ${ac.bg} ${ac.text} border ${ac.border}`}>
                              {agent.display_name}
                            </span>
                          );
                        })}
                      {user.accessible_agents.filter(a => a.id !== defaultAgent?.id).length === 0 && (
                        <span className="text-xs text-gray-400 italic">None</span>
                      )}
                    </div>
                  </td>

                  {/* Actions */}
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => { setSelectedUser(user); setShowAccessDialog(true); }}
                      className="text-sm font-medium hover:underline"
                      style={{ color: BRAND_GREEN }}
                    >
                      Manage Access
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Manage Access Dialog */}
      {showAccessDialog && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4">
            {/* Dialog Header */}
            <div className="px-6 py-4 border-b border-gray-200" style={{ backgroundColor: BRAND_GREEN }}>
              <h2 className="text-lg font-bold text-white">Manage Agent Access</h2>
              <p className="text-sm text-green-100">{selectedUser.username} ({selectedUser.email})</p>
            </div>

            <div className="p-6">
              {/* Default Agent */}
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-700 uppercase mb-2">Default Agent</h3>
                {selectedUser.default_agent ? (
                  <div className={`p-3 rounded-lg border-2 ${getAgentColor(selectedUser.default_agent.name).bg} ${getAgentColor(selectedUser.default_agent.name).border}`}>
                    <span className={`font-semibold ${getAgentColor(selectedUser.default_agent.name).text}`}>
                      {selectedUser.default_agent.display_name}
                    </span>
                    <span className="text-xs text-gray-500 ml-2">(active agent for chat)</span>
                  </div>
                ) : (
                  <div className="p-3 rounded-lg border-2 border-red-200 bg-red-50 text-red-700">
                    No default agent assigned
                  </div>
                )}
              </div>

              {/* Agent Access List */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 uppercase mb-2">Agent Access</h3>
                <div className="space-y-2">
                  {assignableAgents.map(agent => {
                    const hasAccess = selectedUser.accessible_agents.some(a => a.id === agent.id);
                    const isDefault = selectedUser.default_agent?.id === agent.id;
                    const colors = getAgentColor(agent.name);

                    return (
                      <div
                        key={agent.id}
                        className={`flex items-center justify-between p-3 rounded-lg border ${hasAccess ? colors.border + ' ' + colors.bg : 'border-gray-200 bg-gray-50'}`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-3 h-3 rounded-full ${hasAccess ? colors.badge : 'bg-gray-300'}`}></div>
                          <div>
                            <span className={`text-sm font-medium ${hasAccess ? colors.text : 'text-gray-500'}`}>
                              {agent.display_name}
                            </span>
                            {isDefault && (
                              <span className="ml-2 px-2 py-0.5 rounded text-xs bg-green-100 text-green-800 font-medium">
                                DEFAULT
                              </span>
                            )}
                            <p className="text-xs text-gray-500">{agent.tools?.length || 0} tools</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {!isDefault && hasAccess && (
                            <button
                              onClick={() => handleSetDefaultAgent(selectedUser.id, agent.id)}
                              className="px-3 py-1 text-xs rounded border border-gray-300 hover:bg-gray-100 text-gray-700"
                            >
                              Set Default
                            </button>
                          )}
                          {hasAccess && !isDefault ? (
                            <button
                              onClick={() => handleRevokeAccess(selectedUser.id, agent.id)}
                              className="px-3 py-1 text-xs rounded bg-red-100 text-red-700 hover:bg-red-200"
                            >
                              Revoke
                            </button>
                          ) : !hasAccess ? (
                            <button
                              onClick={() => handleGrantAccess(selectedUser.id, agent.id)}
                              className="px-3 py-1 text-xs rounded text-white hover:opacity-90"
                              style={{ backgroundColor: BRAND_GREEN }}
                            >
                              Grant Access
                            </button>
                          ) : null}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Dialog Footer */}
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
              <button
                onClick={() => { setShowAccessDialog(false); setSelectedUser(null); }}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
