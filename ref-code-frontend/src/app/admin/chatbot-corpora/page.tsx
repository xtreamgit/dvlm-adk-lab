'use client';

import { useState, useEffect } from 'react';
import { getAuthHeaders, getAuthHeadersOnly } from '../../../lib/auth-headers';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || '';

interface Corpus { id: number; name: string; display_name: string; description: string | null; is_active: boolean; }
interface ChatbotGroup { id: number; name: string; }
interface CorpusAccess { id: number; chatbot_group_id: number; group_name: string; corpus_id: number; corpus_name: string; corpus_display_name: string; permission: string; granted_at: string; }

export default function ChatbotCorporaPage() {
  const [corpora, setCorpora] = useState<Corpus[]>([]);
  const [groups, setGroups] = useState<ChatbotGroup[]>([]);
  const [access, setAccess] = useState<CorpusAccess[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showGrantDialog, setShowGrantDialog] = useState(false);
  const [selectedCorpus, setSelectedCorpus] = useState<Corpus | null>(null);
  const [grantForm, setGrantForm] = useState({ chatbot_group_id: 0, permission: 'query' });

  const permissionLevels = ['query', 'read', 'upload', 'delete', 'admin'];

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [corporaData, groupsData, accessData] = await Promise.all([
        fetch(`${BACKEND_URL}/api/admin/chatbot/available-corpora`, { headers: getAuthHeadersOnly() }).then(r => r.json()),
        fetch(`${BACKEND_URL}/api/admin/chatbot/groups`, { headers: getAuthHeadersOnly() }).then(r => r.json()),
        fetch(`${BACKEND_URL}/api/admin/chatbot/corpus-access`, { headers: getAuthHeadersOnly() }).then(r => r.json()),
      ]);
      setCorpora(corporaData);
      setGroups(groupsData);
      setAccess(accessData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  const handleGrant = async () => {
    if (!selectedCorpus || !grantForm.chatbot_group_id) { alert('Select a group'); return; }
    try {
      await fetch(`${BACKEND_URL}/api/admin/chatbot/corpus-access`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ chatbot_group_id: grantForm.chatbot_group_id, corpus_id: selectedCorpus.id, permission: grantForm.permission }),
      });
      setShowGrantDialog(false);
      await loadData();
    } catch { alert('Failed'); }
  };

  const handleRevoke = async (groupId: number, corpusId: number) => {
    if (!confirm('Revoke access?')) return;
    try {
      await fetch(`${BACKEND_URL}/api/admin/chatbot/corpus-access/${groupId}/${corpusId}`, {
        method: 'DELETE',
        headers: getAuthHeadersOnly(),
      });
      await loadData();
    } catch { alert('Failed'); }
  };

  const openGrantDialog = (corpus: Corpus) => {
    setSelectedCorpus(corpus);
    setGrantForm({ chatbot_group_id: 0, permission: 'query' });
    setShowGrantDialog(true);
  };

  const getPermColor = (p: string) => {
    switch (p) { case 'query': return 'bg-gray-100 text-gray-800'; case 'read': return 'bg-blue-100 text-blue-800'; case 'upload': return 'bg-green-100 text-green-800'; case 'delete': return 'bg-orange-100 text-orange-800'; case 'admin': return 'bg-red-100 text-red-800'; default: return 'bg-gray-100'; }
  };

  const getCorpusAccess = (corpusId: number) => access.filter(a => a.corpus_id === corpusId);

  if (loading) return <div className="flex items-center justify-center min-h-screen"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  if (error) return <div className="flex items-center justify-center min-h-screen text-red-600">{error}</div>;

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Chatbot Corpora Access</h1>
        <p className="text-gray-600">Manage which chatbot groups can access which corpora</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {corpora.length === 0 ? (
          <div className="col-span-full bg-white rounded-lg shadow p-8 text-center text-gray-500">No corpora available.</div>
        ) : corpora.map((corpus) => {
          const corpusAccess = getCorpusAccess(corpus.id);
          return (
            <div key={corpus.id} className="bg-gray-100 rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 bg-blue-500 border-b flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-semibold text-white">📚 {corpus.display_name || corpus.name}</h3>
                  <p className="text-sm text-blue-100">{corpus.name}</p>
                </div>
                <button onClick={() => openGrantDialog(corpus)} className="text-white hover:text-blue-50 text-sm font-medium bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded">+ Grant</button>
              </div>
              <div className="p-4">
                <div className="text-xs text-gray-500 uppercase font-medium mb-2">Access ({corpusAccess.length})</div>
                {corpusAccess.length === 0 ? (
                  <p className="text-gray-400 italic text-sm">No access granted</p>
                ) : (
                  <div className="space-y-2">
                    {corpusAccess.map((a) => (
                      <div key={a.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">{a.group_name}</span>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${getPermColor(a.permission)}`}>{a.permission}</span>
                        </div>
                        <button onClick={() => handleRevoke(a.chatbot_group_id, a.corpus_id)} className="text-red-600 hover:text-red-800 text-xs">Revoke</button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {showGrantDialog && selectedCorpus && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Grant Access: {selectedCorpus.display_name || selectedCorpus.name}</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Group *</label>
                <select value={grantForm.chatbot_group_id} onChange={(e) => setGrantForm({...grantForm, chatbot_group_id: parseInt(e.target.value)})} className="w-full px-3 py-2 border rounded-md">
                  <option value={0}>Select...</option>
                  {groups.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Permission</label>
                <select value={grantForm.permission} onChange={(e) => setGrantForm({...grantForm, permission: e.target.value})} className="w-full px-3 py-2 border rounded-md">
                  {permissionLevels.map((l) => <option key={l} value={l}>{l}</option>)}
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setShowGrantDialog(false)} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded">Cancel</button>
              <button onClick={handleGrant} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Grant</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
