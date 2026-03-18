'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api-enhanced';

interface CorpusDetail {
  id: number;
  name: string;
  display_name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  document_count: number;
  metadata: {
    sync_status: string;
    last_synced_at: string | null;
    tags: string | null;
    notes: string | null;
  } | null;
  groups_with_access: Array<{
    group_id: number;
    group_name: string;
    permission: string;
  }>;
}

export default function CorpusManagementPage() {
  const [corpora, setCorpora] = useState<CorpusDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCorpora, setSelectedCorpora] = useState<number[]>([]);
  const [includeInactive, setIncludeInactive] = useState(true);
  const [editingMetadata, setEditingMetadata] = useState<number | null>(null);
  const [metadataForm, setMetadataForm] = useState({ tags: '', notes: '' });

  const loadCorpora = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.admin_getAllCorpora(includeInactive);
      setCorpora(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load corpora');
    } finally {
      setLoading(false);
    }
  }, [includeInactive]);

  useEffect(() => {
    loadCorpora();
  }, [loadCorpora]);

  const handleSync = async () => {
    try {
      setSyncing(true);
      setError(null);
      const result = await apiClient.admin_syncCorpora() as { message: string };
      await loadCorpora();
      alert(`Sync complete: ${result.message}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to sync');
    } finally {
      setSyncing(false);
    }
  };

  const toggleSelection = (id: number) => {
    setSelectedCorpora(prev =>
      prev.includes(id) ? prev.filter(cid => cid !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedCorpora.length === corpora.length) {
      setSelectedCorpora([]);
    } else {
      setSelectedCorpora(corpora.map(c => c.id));
    }
  };

  const handleToggleStatus = async (corpusId: number, currentStatus: boolean) => {
    try {
      await apiClient.admin_updateCorpusStatus(corpusId, !currentStatus);
      await loadCorpora();
    } catch (err) {
      alert(`Failed to update status: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleBulkActivate = async () => {
    if (selectedCorpora.length === 0) return;
    try {
      await apiClient.admin_bulkUpdateStatus(selectedCorpora, true);
      setSelectedCorpora([]);
      await loadCorpora();
    } catch (err) {
      alert(`Bulk activate failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleBulkDeactivate = async () => {
    if (selectedCorpora.length === 0) return;
    try {
      await apiClient.admin_bulkUpdateStatus(selectedCorpora, false);
      setSelectedCorpora([]);
      await loadCorpora();
    } catch (err) {
      alert(`Bulk deactivate failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const startEditMetadata = (corpus: CorpusDetail) => {
    setEditingMetadata(corpus.id);
    setMetadataForm({
      tags: corpus.metadata?.tags || '',
      notes: corpus.metadata?.notes || '',
    });
  };

  const saveMetadata = async (corpusId: number) => {
    try {
      await apiClient.admin_updateCorpusMetadata(corpusId, metadataForm);
      setEditingMetadata(null);
      await loadCorpora();
    } catch (err) {
      alert(`Failed to save metadata: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="p-8">
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Corpus Management</h1>
          <p className="text-gray-600 mt-1">Manage corpora, permissions, and sync status</p>
        </div>
        <div className="flex space-x-3">
          <label className="flex items-center text-sm text-gray-700">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
              className="mr-2"
            />
            Show inactive
          </label>
          <button
            onClick={handleSync}
            disabled={syncing}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center"
          >
            {syncing ? (
              <>
                <span className="animate-spin mr-2">⟳</span>
                Syncing...
              </>
            ) : (
              <>🔄 Sync with Vertex AI</>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Bulk Actions */}
      {selectedCorpora.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg mb-4">
          <div className="flex items-center justify-between">
            <span className="font-medium text-blue-900">
              {selectedCorpora.length} corpus selected
            </span>
            <div className="space-x-2">
              <button
                onClick={handleBulkActivate}
                className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 text-sm"
              >
                Activate
              </button>
              <button
                onClick={handleBulkDeactivate}
                className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 text-sm"
              >
                Deactivate
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Corpus Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-100 border-b">
            <tr>
              <th className="p-3 text-left">
                <input
                  type="checkbox"
                  checked={selectedCorpora.length === corpora.length && corpora.length > 0}
                  onChange={toggleSelectAll}
                  className="rounded"
                />
              </th>
              <th className="p-3 text-left text-sm font-semibold text-gray-700">Name</th>
              <th className="p-3 text-left text-sm font-semibold text-gray-700">Display Name</th>
              <th className="p-3 text-left text-sm font-semibold text-gray-700">Documents</th>
              <th className="p-3 text-left text-sm font-semibold text-gray-700">Groups</th>
              <th className="p-3 text-left text-sm font-semibold text-gray-700">Status</th>
              <th className="p-3 text-left text-sm font-semibold text-gray-700">Last Sync</th>
              <th className="p-3 text-left text-sm font-semibold text-gray-700">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {corpora.map((corpus) => (
              <tr key={corpus.id} className="hover:bg-gray-50">
                <td className="p-3">
                  <input
                    type="checkbox"
                    checked={selectedCorpora.includes(corpus.id)}
                    onChange={() => toggleSelection(corpus.id)}
                    className="rounded"
                  />
                </td>
                <td className="p-3">
                  <div className="font-medium text-gray-900">{corpus.name}</div>
                  {editingMetadata === corpus.id ? (
                    <div className="mt-2 space-y-2">
                      <input
                        type="text"
                        placeholder="Tags (comma-separated)"
                        value={metadataForm.tags}
                        onChange={(e) => setMetadataForm({...metadataForm, tags: e.target.value})}
                        className="w-full px-2 py-1 text-sm border rounded"
                      />
                      <textarea
                        placeholder="Notes"
                        value={metadataForm.notes}
                        onChange={(e) => setMetadataForm({...metadataForm, notes: e.target.value})}
                        className="w-full px-2 py-1 text-sm border rounded"
                        rows={2}
                      />
                      <div className="flex space-x-2">
                        <button
                          onClick={() => saveMetadata(corpus.id)}
                          className="text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => setEditingMetadata(null)}
                          className="text-xs bg-gray-300 text-gray-700 px-3 py-1 rounded hover:bg-gray-400"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    corpus.metadata?.notes && (
                      <div className="text-xs text-gray-500 mt-1">{corpus.metadata.notes}</div>
                    )
                  )}
                </td>
                <td className="p-3 text-gray-700">{corpus.display_name}</td>
                <td className="p-3 text-gray-700">{corpus.document_count}</td>
                <td className="p-3">
                  <div className="flex flex-wrap gap-1">
                    {corpus.groups_with_access.map((group) => (
                      <span
                        key={group.group_id}
                        className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded"
                        title={group.permission}
                      >
                        {group.group_name}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="p-3">
                  <button
                    onClick={() => handleToggleStatus(corpus.id, corpus.is_active)}
                    className={`text-xs px-3 py-1 rounded font-medium ${
                      corpus.is_active
                        ? 'bg-green-100 text-green-800 hover:bg-green-200'
                        : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                    }`}
                  >
                    {corpus.is_active ? 'Active' : 'Inactive'}
                  </button>
                </td>
                <td className="p-3 text-sm text-gray-600">
                  {formatDate(corpus.metadata?.last_synced_at || null)}
                </td>
                <td className="p-3">
                  <button
                    onClick={() => startEditMetadata(corpus)}
                    className="text-blue-600 hover:text-blue-800 text-sm mr-2"
                  >
                    Edit
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {corpora.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No corpora found. Click &quot;Sync with Vertex AI&quot; to import corpora.
          </div>
        )}
      </div>
    </div>
  );
}
