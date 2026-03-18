'use client';

import { useState, useEffect } from 'react';
import { getAuthHeadersOnly } from '../../../lib/auth-headers';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || '';

interface Permission {
  id: number;
  name: string;
  description: string | null;
  category: string;
}

export default function ChatbotPermissionsPage() {
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/admin/chatbot/permissions`, {
        headers: getAuthHeadersOnly(),
      });
      if (!response.ok) throw new Error('Failed to fetch permissions');
      setPermissions(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const getCategoryColor = (cat: string) => {
    switch (cat) {
      case 'corpora': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'agents': return 'bg-green-100 text-green-800 border-green-200';
      case 'tools': return 'bg-purple-100 text-purple-800 border-purple-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (loading) return <div className="flex items-center justify-center min-h-screen"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  if (error) return <div className="flex items-center justify-center min-h-screen text-red-600">{error}</div>;

  const byCategory = permissions.reduce((acc, p) => {
    if (!acc[p.category]) acc[p.category] = [];
    acc[p.category].push(p);
    return acc;
  }, {} as Record<string, Permission[]>);

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Chatbot Permissions</h1>
        <p className="text-gray-600">View all available permissions for chatbot roles</p>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
        <p className="text-yellow-700 text-sm">
          <strong>Note:</strong> Permissions are predefined and assigned to roles. Chatbot users inherit permissions through their group memberships.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {Object.entries(byCategory).map(([category, perms]) => (
          <div key={category} className="bg-white rounded-lg shadow overflow-hidden">
            <div className={`px-6 py-4 border-b ${getCategoryColor(category)}`}>
              <h2 className="text-lg font-semibold capitalize">{category} Permissions ({perms.length})</h2>
            </div>
            <div className="p-4 space-y-3">
              {perms.map((p) => (
                <div key={p.id} className="p-3 bg-gray-50 rounded-lg">
                  <div className="font-medium text-gray-900">{p.name}</div>
                  {p.description && <div className="text-sm text-gray-500 mt-1">{p.description}</div>}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
