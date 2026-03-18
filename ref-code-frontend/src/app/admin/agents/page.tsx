'use client';

import { useState, useEffect } from 'react';
import { getAuthHeaders, getAuthHeadersOnly } from '../../../lib/auth-headers';
import { useAgentPermissions } from '@/hooks/useAgentPermissions';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || '';

interface Permission {
  id: number;
  name: string;
  description: string | null;
  category: string;
}

interface ChatbotRole {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  permissions: Permission[];
}

export default function ChatbotRolesPage() {
  const [roles, setRoles] = useState<ChatbotRole[]>([]);
  const [allPermissions, setAllPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showPermDialog, setShowPermDialog] = useState(false);
  const [selectedRole, setSelectedRole] = useState<ChatbotRole | null>(null);
  const [createForm, setCreateForm] = useState({ name: '', description: '' });
  const [editForm, setEditForm] = useState({ name: '', description: '' });
  
  // Get user's agent permissions
  const { permissions: userPermissions, loading: permLoading } = useAgentPermissions();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [rolesData, permsData] = await Promise.all([
        fetch(`${BACKEND_URL}/api/admin/chatbot/roles`, { headers: getAuthHeadersOnly() }).then(r => r.json()),
        fetch(`${BACKEND_URL}/api/admin/chatbot/permissions`, { headers: getAuthHeadersOnly() }).then(r => r.json()),
      ]);
      setRoles(rolesData);
      setAllPermissions(permsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!createForm.name) { alert('Name required'); return; }
    try {
      await fetch(`${BACKEND_URL}/api/admin/chatbot/roles`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(createForm),
      });
      setShowCreateDialog(false);
      setCreateForm({ name: '', description: '' });
      await loadData();
    } catch { alert('Failed to create role'); }
  };

  const handleEdit = async () => {
    if (!selectedRole) return;
    try {
      await fetch(`${BACKEND_URL}/api/admin/chatbot/roles/${selectedRole.id}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(editForm),
      });
      setShowEditDialog(false);
      await loadData();
    } catch { alert('Failed to update role'); }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this role?')) return;
    try {
      await fetch(`${BACKEND_URL}/api/admin/chatbot/roles/${id}`, {
        method: 'DELETE',
        headers: getAuthHeadersOnly(),
      });
      await loadData();
    } catch { alert('Failed to delete'); }
  };

  const handleAddPerm = async (permId: number) => {
    if (!selectedRole) return;
    try {
      await fetch(`${BACKEND_URL}/api/admin/chatbot/roles/${selectedRole.id}/permissions/${permId}`, {
        method: 'POST',
        headers: getAuthHeadersOnly(),
      });
      await loadData();
      setSelectedRole(roles.find(r => r.id === selectedRole.id) || null);
    } catch { alert('Failed'); }
  };

  const handleRemovePerm = async (permId: number) => {
    if (!selectedRole) return;
    try {
      await fetch(`${BACKEND_URL}/api/admin/chatbot/roles/${selectedRole.id}/permissions/${permId}`, {
        method: 'DELETE',
        headers: getAuthHeadersOnly(),
      });
      await loadData();
    } catch { alert('Failed'); }
  };

  const openEditDialog = (role: ChatbotRole) => {
    setSelectedRole(role);
    setEditForm({ name: role.name, description: role.description || '' });
    setShowEditDialog(true);
  };

  const openPermDialog = (role: ChatbotRole) => {
    setSelectedRole(role);
    setShowPermDialog(true);
  };

  if (loading) return <div className="flex items-center justify-center min-h-screen"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  if (error) return <div className="flex items-center justify-center min-h-screen text-red-600">{error}</div>;

  const permsByCategory = allPermissions.reduce((acc, p) => {
    if (!acc[p.category]) acc[p.category] = [];
    acc[p.category].push(p);
    return acc;
  }, {} as Record<string, Permission[]>);

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Agents</h1>
          <p className="text-gray-600">Manage agent types and their tool access</p>
        </div>
        <button onClick={() => setShowCreateDialog(true)} className="bg-emerald-800 text-white px-4 py-2 rounded-lg hover:bg-emerald-900">+ Create Agent</button>
      </div>

      {/* User Permission Indicator */}
      {!permLoading && userPermissions && (
        <div className={`mb-6 p-4 rounded-lg border-2 ${
          userPermissions.agentType === 'admin' ? 'bg-purple-50 border-purple-200' :
          userPermissions.agentType === 'content-manager' ? 'bg-amber-50 border-amber-200' :
          userPermissions.agentType === 'contributor' ? 'bg-emerald-50 border-emerald-200' :
          'bg-blue-50 border-blue-200'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🎭</span>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-900">Your Agent Type:</span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    userPermissions.agentType === 'admin' ? 'bg-purple-600 text-white' :
                    userPermissions.agentType === 'content-manager' ? 'bg-amber-600 text-white' :
                    userPermissions.agentType === 'contributor' ? 'bg-emerald-600 text-white' :
                    'bg-blue-600 text-white'
                  }`}>
                    {userPermissions.agentType === 'admin' ? 'Admin Agent' : userPermissions.agentType?.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  You have access to <strong>{userPermissions.toolCount}</strong> tools
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-500">Available Tools:</p>
              <div className="flex flex-wrap gap-1 mt-1 justify-end max-w-md">
                {userPermissions.allowedTools.slice(0, 6).map((tool) => (
                  <span key={tool} className="px-2 py-0.5 rounded text-xs bg-white border border-gray-300 text-gray-700">
                    {tool}
                  </span>
                ))}
                {userPermissions.allowedTools.length > 6 && (
                  <span className="text-xs text-gray-500">+{userPermissions.allowedTools.length - 6} more</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Agent</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {roles.length === 0 ? (
              <tr><td colSpan={3} className="px-6 py-8 text-center text-gray-500">No agents yet.</td></tr>
            ) : roles.map((role) => (
              <tr key={role.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{role.name}</td>
                <td className="px-6 py-4 text-sm text-gray-500">{role.description || '-'}</td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                  <button onClick={() => openEditDialog(role)} className="text-blue-600 hover:text-blue-900 mr-3">Edit</button>
                  <button onClick={() => handleDelete(role.id)} className="text-red-600 hover:text-red-900">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Agent Type Definitions Section */}
      <div className="mt-12">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Agent Type Definitions</h2>
          <p className="text-gray-600">Standard agent types with predefined tool access levels</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Viewer Agent */}
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl shadow-lg overflow-hidden border border-blue-200">
            <div className="bg-blue-600 px-6 py-4">
              <h3 className="text-xl font-bold text-white">Viewer Agent</h3>
              <p className="text-blue-100 text-sm">Read-only access for general users</p>
            </div>
            <div className="p-6">
              <div className="mb-4">
                <h4 className="text-sm font-semibold text-gray-700 uppercase mb-2">Tools</h4>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                    <span className="text-sm text-gray-700"><code className="bg-blue-100 px-2 py-0.5 rounded text-xs">rag_query</code> - Query documents</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                    <span className="text-sm text-gray-700"><code className="bg-blue-100 px-2 py-0.5 rounded text-xs">list_corpora</code> - List available corpora</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                    <span className="text-sm text-gray-700"><code className="bg-blue-100 px-2 py-0.5 rounded text-xs">get_corpus_info</code> - Get corpus details</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                    <span className="text-sm text-gray-700"><code className="bg-blue-100 px-2 py-0.5 rounded text-xs">browse_documents</code> - Browse document links</span>
                  </div>
                </div>
              </div>
              <div className="mt-4 p-3 bg-white rounded-lg border border-blue-200">
                <p className="text-xs text-gray-600"><strong>Rationale:</strong> Minimum viable toolset for querying and viewing information. Cannot modify any data.</p>
              </div>
            </div>
          </div>

          {/* Contributor Agent */}
          <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-xl shadow-lg overflow-hidden border border-emerald-200">
            <div className="bg-emerald-600 px-6 py-4">
              <h3 className="text-xl font-bold text-white">Contributor Agent</h3>
              <p className="text-emerald-100 text-sm">Users who can add content</p>
            </div>
            <div className="p-6">
              <div className="mb-4">
                <h4 className="text-sm font-semibold text-gray-700 uppercase mb-2">Tools</h4>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
                    <span className="text-sm text-gray-700 italic">All Viewer Agent tools</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
                    <span className="text-sm text-gray-700"><code className="bg-emerald-100 px-2 py-0.5 rounded text-xs">add_data</code> - Add documents to corpora</span>
                  </div>
                </div>
              </div>
              <div className="mt-4 p-3 bg-white rounded-lg border border-emerald-200">
                <p className="text-xs text-gray-600"><strong>Rationale:</strong> All viewer tools + ability to add documents. Cannot create/delete corpora or documents.</p>
              </div>
            </div>
          </div>

          {/* Content Manager Agent */}
          <div className="bg-gradient-to-br from-amber-50 to-amber-100 rounded-xl shadow-lg overflow-hidden border border-amber-200">
            <div className="bg-amber-600 px-6 py-4">
              <h3 className="text-xl font-bold text-white">Content Manager Agent</h3>
              <p className="text-amber-100 text-sm">Manage documents within existing corpora</p>
            </div>
            <div className="p-6">
              <div className="mb-4">
                <h4 className="text-sm font-semibold text-gray-700 uppercase mb-2">Tools</h4>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-amber-500 rounded-full"></span>
                    <span className="text-sm text-gray-700 italic">All Contributor Agent tools</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-amber-500 rounded-full"></span>
                    <span className="text-sm text-gray-700"><code className="bg-amber-100 px-2 py-0.5 rounded text-xs">delete_document</code> - Delete specific documents</span>
                  </div>
                </div>
              </div>
              <div className="mt-4 p-3 bg-white rounded-lg border border-amber-200">
                <p className="text-xs text-gray-600"><strong>Rationale:</strong> Contributor tools + document deletion. Can manage content but not corpus structure.</p>
              </div>
            </div>
          </div>

          {/* Admin Agent */}
          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl shadow-lg overflow-hidden border border-purple-200">
            <div className="bg-purple-600 px-6 py-4">
              <h3 className="text-xl font-bold text-white">Admin Agent</h3>
              <p className="text-purple-100 text-sm">Full corpus lifecycle management</p>
            </div>
            <div className="p-6">
              <div className="mb-4">
                <h4 className="text-sm font-semibold text-gray-700 uppercase mb-2">Tools</h4>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
                    <span className="text-sm text-gray-700 italic">All Content Manager Agent tools</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
                    <span className="text-sm text-gray-700"><code className="bg-purple-100 px-2 py-0.5 rounded text-xs">create_corpus</code> - Create new corpora</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
                    <span className="text-sm text-gray-700"><code className="bg-purple-100 px-2 py-0.5 rounded text-xs">delete_corpus</code> - Delete entire corpora</span>
                  </div>
                </div>
              </div>
              <div className="mt-4 p-3 bg-white rounded-lg border border-purple-200">
                <p className="text-xs text-gray-600"><strong>Rationale:</strong> <strong>ALL TOOLS</strong> - Complete control over corpora and documents. For administrators only.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {showCreateDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Create Agent</h2>
            <div className="space-y-4">
              <div><label className="block text-sm font-medium mb-1">Name *</label><input type="text" value={createForm.name} onChange={(e) => setCreateForm({...createForm, name: e.target.value})} className="w-full px-3 py-2 border rounded-md" /></div>
              <div><label className="block text-sm font-medium mb-1">Description</label><textarea value={createForm.description} onChange={(e) => setCreateForm({...createForm, description: e.target.value})} className="w-full px-3 py-2 border rounded-md" rows={2} /></div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setShowCreateDialog(false)} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded">Cancel</button>
              <button onClick={handleCreate} className="px-4 py-2 bg-emerald-800 text-white rounded hover:bg-emerald-900">Create</button>
            </div>
          </div>
        </div>
      )}

      {showEditDialog && selectedRole && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Edit: {selectedRole.name}</h2>
            <div className="space-y-4">
              <div><label className="block text-sm font-medium mb-1">Name</label><input type="text" value={editForm.name} onChange={(e) => setEditForm({...editForm, name: e.target.value})} className="w-full px-3 py-2 border rounded-md" /></div>
              <div><label className="block text-sm font-medium mb-1">Description</label><textarea value={editForm.description} onChange={(e) => setEditForm({...editForm, description: e.target.value})} className="w-full px-3 py-2 border rounded-md" rows={2} /></div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setShowEditDialog(false)} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded">Cancel</button>
              <button onClick={handleEdit} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Save</button>
            </div>
          </div>
        </div>
      )}

      {showPermDialog && selectedRole && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">Permissions: {selectedRole.name}</h2>
            <div className="mb-4">
              <h3 className="font-medium mb-2">Assigned ({selectedRole.permissions.length})</h3>
              <div className="flex flex-wrap gap-2">
                {selectedRole.permissions.length === 0 ? <span className="text-gray-400 italic">None</span> : selectedRole.permissions.map((p) => (
                  <span key={p.id} className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-green-100 text-green-800">
                    {p.name}<button onClick={() => handleRemovePerm(p.id)} className="ml-2">&times;</button>
                  </span>
                ))}
              </div>
            </div>
            <div>
              <h3 className="font-medium mb-2">Available by Category</h3>
              {Object.entries(permsByCategory).map(([cat, perms]) => (
                <div key={cat} className="mb-3">
                  <div className="text-sm font-medium text-gray-500 capitalize mb-1">{cat}</div>
                  <div className="flex flex-wrap gap-2">
                    {perms.filter(p => !selectedRole.permissions.some(sp => sp.id === p.id)).map((p) => (
                      <button key={p.id} onClick={() => handleAddPerm(p.id)} className="px-3 py-1 rounded-full text-sm bg-gray-100 hover:bg-gray-200">+ {p.name}</button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="flex justify-end mt-6">
              <button onClick={() => setShowPermDialog(false)} className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300">Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
