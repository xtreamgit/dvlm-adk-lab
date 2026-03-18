'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-enhanced';

interface Corpus {
  id: number;
  name: string;
  display_name: string;
}

interface AuditLog {
  id: number;
  corpus_id: number | null;
  corpus_name: string | null;
  user_id: number | null;
  user_name: string | null;
  action: string;
  changes: any;
  metadata: any;
  timestamp: string;
}

export default function AdminAuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [corpora, setCorpora] = useState<Corpus[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingCorpora, setLoadingCorpora] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState({
    action: '',
    userId: '',
    corpusId: '',
  });

  useEffect(() => {
    loadCorpora();
  }, []);

  useEffect(() => {
    loadLogs();
  }, [page]);

  const loadCorpora = async () => {
    try {
      setLoadingCorpora(true);
      const data = await apiClient.admin_getAllCorpora(true);
      setCorpora(data);
    } catch (err) {
      console.error('Failed to load corpora:', err);
    } finally {
      setLoadingCorpora(false);
    }
  };

  const loadLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      // Calculate offset: (page - 1) * limit
      const offset = (page - 1) * 50;
      const data = await apiClient.admin_getAuditLog({ offset, limit: 50 });
      setLogs(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage);
      console.error('Load audit logs error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatChanges = (changes: any) => {
    if (!changes) return null;
    
    // If already an object, stringify it directly
    if (typeof changes === 'object') {
      return (
        <pre className="text-xs bg-gray-100 p-2 rounded max-w-md overflow-auto">
          {JSON.stringify(changes, null, 2)}
        </pre>
      );
    }
    
    // If string, try to parse it
    try {
      const parsed = JSON.parse(changes);
      return (
        <pre className="text-xs bg-gray-100 p-2 rounded max-w-md overflow-auto">
          {JSON.stringify(parsed, null, 2)}
        </pre>
      );
    } catch {
      return <span className="text-xs text-gray-600">{String(changes)}</span>;
    }
  };

  const getActionBadgeColor = (action: string) => {
    const actionLower = action.toLowerCase();
    if (actionLower.includes('create')) return 'bg-green-100 text-green-800';
    if (actionLower.includes('update') || actionLower.includes('edit')) return 'bg-blue-100 text-blue-800';
    if (actionLower.includes('delete') || actionLower.includes('deactivate')) return 'bg-red-100 text-red-800';
    if (actionLower.includes('grant') || actionLower.includes('assign')) return 'bg-purple-100 text-purple-800';
    if (actionLower.includes('revoke') || actionLower.includes('remove')) return 'bg-orange-100 text-orange-800';
    return 'bg-gray-100 text-gray-800';
  };

  const filteredLogs = logs.filter((log) => {
    if (filter.action && !log.action.toLowerCase().includes(filter.action.toLowerCase())) {
      return false;
    }
    if (filter.userId && log.user_id?.toString() !== filter.userId) {
      return false;
    }
    if (filter.corpusId && log.corpus_id?.toString() !== filter.corpusId) {
      return false;
    }
    return true;
  });

  if (loading && logs.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading audit logs...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">Error</div>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={loadLogs}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Audit Logs</h1>
        <p className="text-gray-600">System activity and change history</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Filters</h2>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Action
            </label>
            <input
              type="text"
              value={filter.action}
              onChange={(e) => setFilter({ ...filter, action: e.target.value })}
              placeholder="e.g., created, updated..."
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              User ID
            </label>
            <input
              type="text"
              value={filter.userId}
              onChange={(e) => setFilter({ ...filter, userId: e.target.value })}
              placeholder="Filter by user ID"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Corpus
            </label>
            <select
              value={filter.corpusId}
              onChange={(e) => setFilter({ ...filter, corpusId: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md"
              disabled={loadingCorpora}
            >
              <option value="">All corpora</option>
              {corpora.map((corpus) => (
                <option key={corpus.id} value={corpus.id}>
                  {corpus.display_name || corpus.name}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="mt-3 flex justify-end">
          <button
            onClick={() => setFilter({ action: '', userId: '', corpusId: '' })}
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Action
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Corpus
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Changes
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    No audit logs found
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(log.timestamp)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.user_name || `User ${log.user_id || 'N/A'}`}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getActionBadgeColor(
                          log.action
                        )}`}
                      >
                        {log.action}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.corpus_name || (log.corpus_id ? `Corpus ${log.corpus_id}` : '-')}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {formatChanges(log.changes)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Showing <span className="font-medium">{filteredLogs.length}</span> logs
            {filter.action || filter.userId || filter.corpusId ? ' (filtered)' : ''}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className={`px-4 py-2 text-sm rounded ${
                page === 1
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              Previous
            </button>
            <span className="px-4 py-2 text-sm text-gray-700">
              Page {page}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={logs.length < 50}
              className={`px-4 py-2 text-sm rounded ${
                logs.length < 50
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
