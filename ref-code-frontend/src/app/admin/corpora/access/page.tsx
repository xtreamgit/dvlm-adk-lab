'use client';

import { useState, useEffect } from 'react';
import { getAuthHeaders, getAuthHeadersOnly } from '../../../../lib/auth-headers';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || '';

interface Corpus {
  id: number;
  name: string;
  display_name: string;
  description: string | null;
  is_active: boolean;
  document_count: number;
}

interface ChatbotGroup {
  id: number;
  name: string;
}

interface CorpusAccess {
  id: number;
  chatbot_group_id: number;
  group_name: string;
  corpus_id: number;
  corpus_name: string;
  corpus_display_name: string;
  permission: string;
  granted_at: string;
}

export default function CorporaGroupAccessPage() {
  const [corpora, setCorpora] = useState<Corpus[]>([]);
  const [groups, setGroups] = useState<ChatbotGroup[]>([]);
  const [access, setAccess] = useState<CorpusAccess[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const targetGroups = ['admin-group', 'content-manager-group', 'contributor-group', 'viewer-group'];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [corporaData, groupsData, accessData] = await Promise.all([
        fetch(`${BACKEND_URL}/api/admin/chatbot/available-corpora`, {
          headers: getAuthHeadersOnly()
        }).then(r => r.json()),
        fetch(`${BACKEND_URL}/api/admin/chatbot/groups`, {
          headers: getAuthHeadersOnly()
        }).then(r => r.json()),
        fetch(`${BACKEND_URL}/api/admin/chatbot/corpus-access`, {
          headers: getAuthHeadersOnly()
        }).then(r => r.json()),
      ]);
      setCorpora(corporaData);
      setGroups(groupsData);
      setAccess(accessData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const hasAccess = (corpusId: number, groupName: string): boolean => {
    return access.some(a => a.corpus_id === corpusId && a.group_name === groupName);
  };

  const toggleAccess = async (corpusId: number, groupName: string) => {
    const groupId = groups.find(g => g.name === groupName)?.id;
    if (!groupId) {
      console.error('Group not found:', groupName);
      return;
    }

    const currentAccess = hasAccess(corpusId, groupName);
    
    try {
      if (currentAccess) {
        // Revoke access
        const response = await fetch(`${BACKEND_URL}/api/admin/chatbot/corpus-access/${groupId}/${corpusId}`, {
          method: 'DELETE',
          headers: getAuthHeadersOnly()
        });
        
        if (!response.ok) throw new Error('Failed to revoke access');
        
        // Update state without full page reload
        const updatedAccess = await fetch(`${BACKEND_URL}/api/admin/chatbot/corpus-access`, {
          headers: getAuthHeadersOnly()
        }).then(r => r.json());
        setAccess(updatedAccess);
      } else {
        // Grant access
        const response = await fetch(`${BACKEND_URL}/api/admin/chatbot/corpus-access`, {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({
            chatbot_group_id: groupId,
            corpus_id: corpusId,
            permission: 'query'
          })
        });
        
        if (!response.ok) throw new Error('Failed to grant access');
        
        // Update state without full page reload
        const updatedAccess = await fetch(`${BACKEND_URL}/api/admin/chatbot/corpus-access`, {
          headers: getAuthHeadersOnly()
        }).then(r => r.json());
        setAccess(updatedAccess);
      }
    } catch (err) {
      console.error('Error toggling access:', err);
      setError(err instanceof Error ? err.message : 'Failed to toggle access');
    }
  };

  // Calculate statistics
  const activeCorpora = corpora.filter(c => c.is_active).length;
  const groupsCount = targetGroups.length;
  const totalPermissions = access.length;
  const possibleCombinations = corpora.length * targetGroups.length;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen text-red-600">
        {error}
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Corpora to Group Access</h1>
        <p className="text-gray-600">View corpus access permissions across chatbot groups</p>
      </div>

      {/* Access Summary */}
      <div className="mb-6 bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Access Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-4xl font-bold text-blue-600 mb-2">{activeCorpora}</div>
            <div className="text-sm text-gray-600">Active Corpora</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-purple-600 mb-2">{groupsCount}</div>
            <div className="text-sm text-gray-600">Groups</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-emerald-600 mb-2">{totalPermissions}</div>
            <div className="text-sm text-gray-600">Total Permissions</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-orange-600 mb-2">{possibleCombinations}</div>
            <div className="text-sm text-gray-600">Possible Combinations</div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="mb-6 bg-white rounded-lg shadow p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Legend</h3>
        <div className="flex gap-6">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-emerald-700 rounded flex items-center justify-center">
              <span className="text-white text-sm">✓</span>
            </div>
            <span className="text-sm text-gray-700">Has Access</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gray-200 rounded"></div>
            <span className="text-sm text-gray-700">No Access</span>
          </div>
        </div>
      </div>

      {/* Access Matrix Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 sticky left-0 bg-gray-50 z-10 border-r-2 border-gray-300">
                  Corpus
                </th>
                {targetGroups.map(groupName => (
                  <th key={groupName} className="px-6 py-4 text-center text-sm font-semibold text-gray-700">
                    {groupName}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {corpora.length === 0 ? (
                <tr>
                  <td colSpan={targetGroups.length + 1} className="px-6 py-8 text-center text-gray-500">
                    No corpora available
                  </td>
                </tr>
              ) : (
                corpora.map((corpus) => (
                  <tr key={corpus.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 sticky left-0 bg-white z-10 border-r-2 border-gray-300">
                      <div>
                        <div className="text-sm font-semibold text-gray-900">
                          {corpus.display_name || corpus.name} <span className="text-gray-500 font-normal">({corpus.document_count})</span>
                        </div>
                        <div className="text-xs text-gray-500">{corpus.name}</div>
                      </div>
                    </td>
                    {targetGroups.map(groupName => {
                      const hasGroupAccess = hasAccess(corpus.id, groupName);
                      return (
                        <td key={groupName} className="px-6 py-4 text-center">
                          <div className="flex justify-center">
                            {hasGroupAccess ? (
                              <div 
                                className="w-10 h-10 bg-emerald-700 rounded flex items-center justify-center cursor-pointer hover:bg-emerald-800 transition-colors"
                                onClick={() => toggleAccess(corpus.id, groupName)}
                                title="Click to revoke access"
                              >
                                <span className="text-white font-bold">✓</span>
                              </div>
                            ) : (
                              <div 
                                className="w-10 h-10 bg-gray-200 rounded cursor-pointer hover:bg-gray-300 transition-colors"
                                onClick={() => toggleAccess(corpus.id, groupName)}
                                title="Click to grant access"
                              ></div>
                            )}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
