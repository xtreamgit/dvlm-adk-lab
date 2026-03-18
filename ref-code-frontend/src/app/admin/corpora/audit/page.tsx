'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api-enhanced';

interface Corpus {
  id: number;
  name: string;
  display_name: string;
}

interface AuditEntry {
  id: number;
  corpus_id: number | null;
  corpus_name: string | null;
  user_id: number | null;
  user_name: string | null;
  action: string;
  changes: string | null;
  metadata: string | null;
  timestamp: string;
}

export default function AuditLogPage() {
  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const [corpora, setCorpora] = useState<Corpus[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingCorpora, setLoadingCorpora] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    corpus_id: '',
    action: '',
    limit: 100,
  });
  const [expandedLog, setExpandedLog] = useState<number | null>(null);

  const loadCorpora = async () => {
    try {
      setLoadingCorpora(true);
      const data = await apiClient.admin_getAllCorpora(true); // Include inactive
      setCorpora(data);
    } catch (err) {
      console.error('Failed to load corpora:', err);
    } finally {
      setLoadingCorpora(false);
    }
  };

  const loadAuditLog = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const filterParams: Record<string, string | number> = { limit: filters.limit };
      if (filters.corpus_id) filterParams.corpus_id = parseInt(filters.corpus_id);
      if (filters.action) filterParams.action = filters.action;

      const data = await apiClient.admin_getAuditLog(filterParams);
      setLogs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audit log');
    } finally {
      setLoading(false);
    }
  }, [filters.limit, filters.corpus_id, filters.action]);

  useEffect(() => {
    loadCorpora();
    loadAuditLog();
  }, [loadAuditLog]);

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const applyFilters = () => {
    loadAuditLog();
  };

  const clearFilters = () => {
    setFilters({ corpus_id: '', action: '', limit: 100 });
    setTimeout(() => loadAuditLog(), 0);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getActionColor = (action: string): string => {
    switch (action) {
      case 'created': return 'bg-green-100 text-green-800';
      case 'updated': return 'bg-blue-100 text-blue-800';
      case 'deleted': return 'bg-red-100 text-red-800';
      case 'granted_access': return 'bg-purple-100 text-purple-800';
      case 'revoked_access': return 'bg-orange-100 text-orange-800';
      case 'activated': return 'bg-green-100 text-green-800';
      case 'deactivated': return 'bg-gray-100 text-gray-800';
      case 'synced': return 'bg-cyan-100 text-cyan-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const toggleExpand = (logId: number) => {
    setExpandedLog(expandedLog === logId ? null : logId);
  };

  const parseJSON = (jsonString: string | null) => {
    if (!jsonString) return null;
    try {
      return JSON.parse(jsonString);
    } catch {
      return jsonString;
    }
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
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Audit Log</h1>
        <p className="text-gray-600 mt-1">
          Track all changes to corpora, permissions, and access control
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <h3 className="font-semibold text-gray-900 mb-3">Filters</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Corpus
            </label>
            <select
              value={filters.corpus_id}
              onChange={(e) => handleFilterChange('corpus_id', e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Action Type
            </label>
            <select
              value={filters.action}
              onChange={(e) => handleFilterChange('action', e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Actions</option>
              <option value="created">Created</option>
              <option value="updated">Updated</option>
              <option value="deleted">Deleted</option>
              <option value="granted_access">Granted Access</option>
              <option value="revoked_access">Revoked Access</option>
              <option value="activated">Activated</option>
              <option value="deactivated">Deactivated</option>
              <option value="synced">Synced</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Limit
            </label>
            <select
              value={filters.limit}
              onChange={(e) => handleFilterChange('limit', e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="50">50 entries</option>
              <option value="100">100 entries</option>
              <option value="200">200 entries</option>
              <option value="500">500 entries</option>
            </select>
          </div>
          <div className="flex items-end space-x-2">
            <button
              onClick={applyFilters}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Apply
            </button>
            <button
              onClick={clearFilters}
              className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
            >
              Clear
            </button>
          </div>
        </div>
      </div>

      {/* Audit Log Entries */}
      <div className="space-y-3">
        {logs.map((log) => {
          const isExpanded = expandedLog === log.id;
          const changes = parseJSON(log.changes);

          return (
            <div key={log.id} className="bg-white rounded-lg shadow overflow-hidden">
              <div className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <span className={`text-xs px-3 py-1 rounded font-medium ${getActionColor(log.action)}`}>
                        {log.action}
                      </span>
                      {log.user_name && (
                        <span className="text-sm text-gray-700 font-medium">
                          by {log.user_name}
                        </span>
                      )}
                      {log.corpus_name && (
                        <span className="text-sm text-gray-600">
                          on <span className="font-mono">{log.corpus_name}</span>
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatDate(log.timestamp)}
                    </div>
                  </div>
                  {changes && (
                    <button
                      onClick={() => toggleExpand(log.id)}
                      className="text-blue-600 hover:text-blue-800 text-sm ml-4"
                    >
                      {isExpanded ? 'Hide Details' : 'Show Details'}
                    </button>
                  )}
                </div>

                {/* Expanded Details */}
                {isExpanded && changes && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">Changes:</h4>
                    <pre className="bg-gray-50 p-3 rounded text-xs overflow-x-auto">
                      {JSON.stringify(changes, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {logs.length === 0 && (
        <div className="bg-white rounded-lg shadow p-12 text-center text-gray-500">
          No audit log entries found.
        </div>
      )}

      {/* Summary */}
      <div className="mt-6 bg-white rounded-lg shadow p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Statistics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{logs.length}</div>
            <div className="text-sm text-gray-600">Entries Loaded</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {logs.filter(l => l.action === 'created').length}
            </div>
            <div className="text-sm text-gray-600">Created</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {logs.filter(l => l.action === 'granted_access').length}
            </div>
            <div className="text-sm text-gray-600">Access Granted</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {logs.filter(l => l.action === 'revoked_access').length}
            </div>
            <div className="text-sm text-gray-600">Access Revoked</div>
          </div>
        </div>
      </div>
    </div>
  );
}
