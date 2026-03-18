'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api-enhanced';

interface BridgeStatus {
  enabled: boolean;
  cache_ttl_seconds: number;
  agent_mappings_count: number;
  corpus_mappings_count: number;
  synced_users_count: number;
  last_sync: string | null;
}

interface AgentMapping {
  id: number;
  google_group_email: string;
  chatbot_group_id: number;
  chatbot_group_name: string | null;
  priority: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface CorpusMapping {
  id: number;
  google_group_email: string;
  corpus_id: number;
  corpus_name: string | null;
  permission: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface ChatbotGroup {
  id: number;
  name: string;
  description: string;
}

interface Corpus {
  id: number;
  name: string;
  display_name: string;
}

const PERMISSIONS = ['query', 'read', 'upload', 'delete', 'admin'];
const BRAND_GREEN = 'rgb(0,84,64)';

export default function GoogleGroupsBridgePage() {
  const [status, setStatus] = useState<BridgeStatus | null>(null);
  const [agentMappings, setAgentMappings] = useState<AgentMapping[]>([]);
  const [corpusMappings, setCorpusMappings] = useState<CorpusMapping[]>([]);
  const [chatbotGroups, setChatbotGroups] = useState<ChatbotGroup[]>([]);
  const [corpora, setCorpora] = useState<Corpus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [activeTab, setActiveTab] = useState<'agent' | 'corpus'>('agent');

  // New mapping form state
  const [newAgentMapping, setNewAgentMapping] = useState({ google_group_email: '', chatbot_group_id: 0, priority: 0 });
  const [newCorpusMapping, setNewCorpusMapping] = useState({ google_group_email: '', corpus_id: 0, permission: 'query' });
  const [showAgentForm, setShowAgentForm] = useState(false);
  const [showCorpusForm, setShowCorpusForm] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [statusRes, agentRes, corpusRes] = await Promise.all([
        apiClient.ggBridge_getStatus(),
        apiClient.ggBridge_listAgentMappings(),
        apiClient.ggBridge_listCorpusMappings(),
      ]);

      setStatus(statusRes);
      setAgentMappings(agentRes);
      setCorpusMappings(corpusRes);

      // Load chatbot groups and corpora for dropdowns
      try {
        const groups = await apiClient.getChatbotGroups();
        if (Array.isArray(groups)) setChatbotGroups(groups);
      } catch { /* ignore */ }

      try {
        const corporaRes = await apiClient.getAllCorporaWithAccess();
        if (Array.isArray(corporaRes)) setCorpora(corporaRes);
      } catch { /* ignore */ }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const showSuccess = (msg: string) => {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(null), 3000);
  };

  const handleCreateAgentMapping = async () => {
    if (!newAgentMapping.google_group_email || !newAgentMapping.chatbot_group_id) {
      setError('Please fill in all required fields');
      return;
    }
    try {
      await apiClient.ggBridge_createAgentMapping(newAgentMapping);
      setNewAgentMapping({ google_group_email: '', chatbot_group_id: 0, priority: 0 });
      setShowAgentForm(false);
      showSuccess('Agent mapping created');
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create mapping');
    }
  };

  const handleDeleteAgentMapping = async (id: number) => {
    if (!confirm('Delete this agent mapping?')) return;
    try {
      await apiClient.ggBridge_deleteAgentMapping(id);
      showSuccess('Agent mapping deleted');
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete mapping');
    }
  };

  const handleToggleAgentMapping = async (mapping: AgentMapping) => {
    try {
      await apiClient.ggBridge_updateAgentMapping(mapping.id, { is_active: !mapping.is_active });
      showSuccess(`Mapping ${mapping.is_active ? 'disabled' : 'enabled'}`);
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update mapping');
    }
  };

  const handleCreateCorpusMapping = async () => {
    if (!newCorpusMapping.google_group_email || !newCorpusMapping.corpus_id) {
      setError('Please fill in all required fields');
      return;
    }
    try {
      await apiClient.ggBridge_createCorpusMapping(newCorpusMapping);
      setNewCorpusMapping({ google_group_email: '', corpus_id: 0, permission: 'query' });
      setShowCorpusForm(false);
      showSuccess('Corpus mapping created');
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create mapping');
    }
  };

  const handleDeleteCorpusMapping = async (id: number) => {
    if (!confirm('Delete this corpus mapping?')) return;
    try {
      await apiClient.ggBridge_deleteCorpusMapping(id);
      showSuccess('Corpus mapping deleted');
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete mapping');
    }
  };

  const handleToggleCorpusMapping = async (mapping: CorpusMapping) => {
    try {
      await apiClient.ggBridge_updateCorpusMapping(mapping.id, { is_active: !mapping.is_active });
      showSuccess(`Mapping ${mapping.is_active ? 'disabled' : 'enabled'}`);
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update mapping');
    }
  };

  const handleSyncAll = async () => {
    try {
      setSyncing(true);
      setError(null);
      const results = await apiClient.ggBridge_syncAllUsers();
      const synced = results.filter((r: any) => r.status === 'synced').length;
      showSuccess(`Synced ${synced}/${results.length} users`);
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to sync');
    } finally {
      setSyncing(false);
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
          <p className="mt-4 text-gray-600">Loading Google Groups Bridge...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Google Groups Bridge</h1>
        <p className="text-gray-500 mb-6">
          Map Google Groups to chatbot groups and corpus access. Users are automatically assigned on login.
        </p>

        {/* Status & Error Messages */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex justify-between items-center">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700 font-bold">×</button>
          </div>
        )}
        {successMsg && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
            {successMsg}
          </div>
        )}

        {/* Status Cards */}
        {status && (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="text-sm font-medium text-gray-500">Status</h3>
              <p className={`text-xl font-bold ${status.enabled ? 'text-green-600' : 'text-yellow-600'}`}>
                {status.enabled ? 'Enabled' : 'Disabled'}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="text-sm font-medium text-gray-500">Agent Mappings</h3>
              <p className="text-xl font-bold" style={{ color: BRAND_GREEN }}>{status.agent_mappings_count}</p>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="text-sm font-medium text-gray-500">Corpus Mappings</h3>
              <p className="text-xl font-bold" style={{ color: BRAND_GREEN }}>{status.corpus_mappings_count}</p>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="text-sm font-medium text-gray-500">Synced Users</h3>
              <p className="text-xl font-bold text-blue-600">{status.synced_users_count}</p>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="text-sm font-medium text-gray-500">Last Sync</h3>
              <p className="text-sm font-medium text-gray-700">{formatDate(status.last_sync)}</p>
            </div>
          </div>
        )}

        {/* Info Banner when disabled */}
        {status && !status.enabled && (
          <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <h3 className="font-semibold text-yellow-800 mb-1">Bridge is Disabled</h3>
            <p className="text-yellow-700 text-sm">
              Set <code className="bg-yellow-100 px-1 rounded">GOOGLE_GROUPS_ENABLED=true</code> in the backend environment to enable automatic sync.
              You can still configure mappings below — they will take effect once the bridge is enabled.
            </p>
          </div>
        )}

        {/* Sync Button */}
        <div className="mb-6 flex gap-3">
          <button
            onClick={handleSyncAll}
            disabled={syncing || !status?.enabled}
            className="px-4 py-2 rounded-lg text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ backgroundColor: BRAND_GREEN }}
          >
            {syncing ? 'Syncing...' : 'Sync All Users'}
          </button>
          <button
            onClick={loadData}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
          >
            Refresh
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 mb-6">
          <button
            onClick={() => setActiveTab('agent')}
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'agent'
                ? 'border-green-700 text-green-800'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Agent Group Mappings ({agentMappings.length})
          </button>
          <button
            onClick={() => setActiveTab('corpus')}
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'corpus'
                ? 'border-green-700 text-green-800'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Corpus Access Mappings ({corpusMappings.length})
          </button>
        </div>

        {/* Agent Mappings Tab */}
        {activeTab === 'agent' && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Google Group → Chatbot Group</h2>
                <p className="text-sm text-gray-500">Maps a Google Group to a chatbot group (agent type). Highest priority wins.</p>
              </div>
              <button
                onClick={() => setShowAgentForm(!showAgentForm)}
                className="px-4 py-2 text-white rounded-lg text-sm font-medium"
                style={{ backgroundColor: BRAND_GREEN }}
              >
                {showAgentForm ? 'Cancel' : '+ Add Mapping'}
              </button>
            </div>

            {/* Add Form */}
            {showAgentForm && (
              <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Google Group Email</label>
                    <input
                      type="email"
                      value={newAgentMapping.google_group_email}
                      onChange={(e) => setNewAgentMapping({ ...newAgentMapping, google_group_email: e.target.value })}
                      placeholder="developers@company.com"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Chatbot Group</label>
                    <select
                      value={newAgentMapping.chatbot_group_id}
                      onChange={(e) => setNewAgentMapping({ ...newAgentMapping, chatbot_group_id: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    >
                      <option value={0}>Select group...</option>
                      {chatbotGroups.map((g) => (
                        <option key={g.id} value={g.id}>{g.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                    <input
                      type="number"
                      value={newAgentMapping.priority}
                      onChange={(e) => setNewAgentMapping({ ...newAgentMapping, priority: parseInt(e.target.value) || 0 })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    />
                  </div>
                  <div className="flex items-end">
                    <button
                      onClick={handleCreateAgentMapping}
                      className="px-4 py-2 text-white rounded-lg text-sm font-medium"
                      style={{ backgroundColor: BRAND_GREEN }}
                    >
                      Create
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Google Group</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Chatbot Group</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Priority</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {agentMappings.map((m) => (
                    <tr key={m.id} className={!m.is_active ? 'opacity-50' : ''}>
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">{m.google_group_email}</td>
                      <td className="px-6 py-4 text-sm text-gray-700">{m.chatbot_group_name || `ID: ${m.chatbot_group_id}`}</td>
                      <td className="px-6 py-4 text-sm text-gray-500">{m.priority}</td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          m.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                        }`}>
                          {m.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">{formatDate(m.created_at)}</td>
                      <td className="px-6 py-4 text-right space-x-2">
                        <button
                          onClick={() => handleToggleAgentMapping(m)}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          {m.is_active ? 'Disable' : 'Enable'}
                        </button>
                        <button
                          onClick={() => handleDeleteAgentMapping(m.id)}
                          className="text-sm text-red-600 hover:text-red-800"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {agentMappings.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No agent group mappings configured. Click &quot;+ Add Mapping&quot; to create one.
                </div>
              )}
            </div>
          </div>
        )}

        {/* Corpus Mappings Tab */}
        {activeTab === 'corpus' && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Google Group → Corpus Access</h2>
                <p className="text-sm text-gray-500">Maps a Google Group to corpus access with a permission level.</p>
              </div>
              <button
                onClick={() => setShowCorpusForm(!showCorpusForm)}
                className="px-4 py-2 text-white rounded-lg text-sm font-medium"
                style={{ backgroundColor: BRAND_GREEN }}
              >
                {showCorpusForm ? 'Cancel' : '+ Add Mapping'}
              </button>
            </div>

            {/* Add Form */}
            {showCorpusForm && (
              <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Google Group Email</label>
                    <input
                      type="email"
                      value={newCorpusMapping.google_group_email}
                      onChange={(e) => setNewCorpusMapping({ ...newCorpusMapping, google_group_email: e.target.value })}
                      placeholder="developers@company.com"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Corpus</label>
                    <select
                      value={newCorpusMapping.corpus_id}
                      onChange={(e) => setNewCorpusMapping({ ...newCorpusMapping, corpus_id: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    >
                      <option value={0}>Select corpus...</option>
                      {corpora.map((c) => (
                        <option key={c.id} value={c.id}>{c.display_name || c.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Permission</label>
                    <select
                      value={newCorpusMapping.permission}
                      onChange={(e) => setNewCorpusMapping({ ...newCorpusMapping, permission: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    >
                      {PERMISSIONS.map((p) => (
                        <option key={p} value={p}>{p}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-end">
                    <button
                      onClick={handleCreateCorpusMapping}
                      className="px-4 py-2 text-white rounded-lg text-sm font-medium"
                      style={{ backgroundColor: BRAND_GREEN }}
                    >
                      Create
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Google Group</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Corpus</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Permission</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {corpusMappings.map((m) => (
                    <tr key={m.id} className={!m.is_active ? 'opacity-50' : ''}>
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">{m.google_group_email}</td>
                      <td className="px-6 py-4 text-sm text-gray-700">{m.corpus_name || `ID: ${m.corpus_id}`}</td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          m.permission === 'admin' ? 'bg-red-100 text-red-800' :
                          m.permission === 'delete' ? 'bg-orange-100 text-orange-800' :
                          m.permission === 'upload' ? 'bg-blue-100 text-blue-800' :
                          m.permission === 'read' ? 'bg-green-100 text-green-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {m.permission}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          m.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                        }`}>
                          {m.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">{formatDate(m.created_at)}</td>
                      <td className="px-6 py-4 text-right space-x-2">
                        <button
                          onClick={() => handleToggleCorpusMapping(m)}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          {m.is_active ? 'Disable' : 'Enable'}
                        </button>
                        <button
                          onClick={() => handleDeleteCorpusMapping(m.id)}
                          className="text-sm text-red-600 hover:text-red-800"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {corpusMappings.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No corpus access mappings configured. Click &quot;+ Add Mapping&quot; to create one.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
