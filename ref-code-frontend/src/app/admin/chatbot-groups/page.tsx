'use client';

import { useState, useEffect } from 'react';
import { getAuthHeaders, getAuthHeadersOnly } from '../../../lib/auth-headers';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || '';

interface ChatbotAgent {
  id: number;
  name: string;
  description?: string;
}

interface ChatbotGroup {
  id: number;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  user_count: number;
  roles: ChatbotAgent[];
}

export default function ChatbotGroupsPage() {
  const [groups, setGroups] = useState<ChatbotGroup[]>([]);
  const [allRoles, setAllRoles] = useState<ChatbotAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showAgentDialog, setShowAgentDialog] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<ChatbotGroup | null>(null);
  const [createForm, setCreateForm] = useState({ name: '', description: '' });
  const [editForm, setEditForm] = useState({ name: '', description: '', is_active: true });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [groupsData, rolesData] = await Promise.all([
        fetchGroups(),
        fetchRoles(),
      ]);
      setGroups(groupsData);
      setAllRoles(rolesData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const fetchGroups = async () => {
    const response = await fetch(`${BACKEND_URL}/api/admin/chatbot/groups`, {
      headers: getAuthHeadersOnly(),
    });
    if (!response.ok) throw new Error('Failed to fetch groups');
    return response.json();
  };

  const fetchRoles = async () => {
    const response = await fetch(`${BACKEND_URL}/api/admin/chatbot/roles`, {
      headers: getAuthHeadersOnly(),
    });
    if (!response.ok) throw new Error('Failed to fetch roles');
    return response.json();
  };

  const handleCreate = async () => {
    if (!createForm.name) { alert('Name is required'); return; }
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/chatbot/groups`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(createForm),
      });
      if (!response.ok) throw new Error('Failed to create group');
      setShowCreateDialog(false);
      setCreateForm({ name: '', description: '' });
      await loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create group');
    }
  };

  const handleEdit = async () => {
    if (!selectedGroup) return;
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/chatbot/groups/${selectedGroup.id}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(editForm),
      });
      if (!response.ok) throw new Error('Failed to update group');
      setShowEditDialog(false);
      await loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update group');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this group?')) return;
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/chatbot/groups/${id}`, {
        method: 'DELETE',
        headers: getAuthHeadersOnly(),
      });
      if (!response.ok) throw new Error('Failed to delete group');
      await loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete group');
    }
  };

  const handleAssignRole = async (roleId: number) => {
    if (!selectedGroup) return;
    try {
      await fetch(`${BACKEND_URL}/api/admin/chatbot/groups/${selectedGroup.id}/roles/${roleId}`, {
        method: 'POST',
        headers: getAuthHeadersOnly(),
      });
      const updatedGroups = await fetchGroups();
      setGroups(updatedGroups);
      // Update selectedGroup with fresh data
      const updatedGroup = updatedGroups.find((g: ChatbotGroup) => g.id === selectedGroup.id);
      if (updatedGroup) setSelectedGroup(updatedGroup);
    } catch (err) {
      alert('Failed to assign role');
    }
  };

  const handleRemoveRole = async (roleId: number) => {
    if (!selectedGroup) return;
    try {
      await fetch(`${BACKEND_URL}/api/admin/chatbot/groups/${selectedGroup.id}/roles/${roleId}`, {
        method: 'DELETE',
        headers: getAuthHeadersOnly(),
      });
      const updatedGroups = await fetchGroups();
      setGroups(updatedGroups);
      // Update selectedGroup with fresh data
      const updatedGroup = updatedGroups.find((g: ChatbotGroup) => g.id === selectedGroup.id);
      if (updatedGroup) setSelectedGroup(updatedGroup);
    } catch (err) {
      alert('Failed to remove role');
    }
  };

  const openEditDialog = (group: ChatbotGroup) => {
    setSelectedGroup(group);
    setEditForm({ name: group.name, description: group.description || '', is_active: group.is_active });
    setShowEditDialog(true);
  };

  const openAgentDialog = (group: ChatbotGroup) => {
    setSelectedGroup(group);
    setShowAgentDialog(true);
  };

  if (loading) return <div className="flex items-center justify-center min-h-screen"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  if (error) return <div className="flex items-center justify-center min-h-screen"><div className="text-red-600">{error}</div><button onClick={loadData} className="ml-4 bg-emerald-800 text-white px-4 py-2 rounded">Retry</button></div>;

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Chatbot Groups</h1>
          <p className="text-gray-600">Manage chatbot user groups and their agent assignments</p>
        </div>
        <button onClick={() => setShowCreateDialog(true)} className="bg-emerald-800 text-white px-4 py-2 rounded-lg hover:bg-emerald-900">+ Create Group</button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Users</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Agent</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {groups.length === 0 ? (
              <tr><td colSpan={5} className="px-6 py-8 text-center text-gray-500">No groups yet.</td></tr>
            ) : groups.map((group) => (
              <tr key={group.id} className="hover:bg-gray-300 even:bg-gray-200">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{group.name}</td>
                <td className="px-6 py-4 text-sm text-gray-500">{group.description || '-'}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{group.user_count}</td>
                <td className="px-6 py-4 text-sm">
                  <div className="flex flex-wrap gap-1">
                    {group.roles.map((r) => (
                      <span key={r.id} className="px-2 py-0.5 rounded text-xs bg-purple-100 text-purple-800">{r.name}</span>
                    ))}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                  <button onClick={() => openAgentDialog(group)} className="text-purple-600 hover:text-purple-900 mr-3">Agent</button>
                  <button onClick={() => openEditDialog(group)} className="text-blue-600 hover:text-blue-900 mr-3">Edit</button>
                  <button onClick={() => handleDelete(group.id)} className="text-red-600 hover:text-red-900">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showCreateDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Create Group</h2>
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

      {showEditDialog && selectedGroup && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Edit: {selectedGroup.name}</h2>
            <div className="space-y-4">
              <div><label className="block text-sm font-medium mb-1">Name</label><input type="text" value={editForm.name} onChange={(e) => setEditForm({...editForm, name: e.target.value})} className="w-full px-3 py-2 border rounded-md" /></div>
              <div><label className="block text-sm font-medium mb-1">Description</label><textarea value={editForm.description} onChange={(e) => setEditForm({...editForm, description: e.target.value})} className="w-full px-3 py-2 border rounded-md" rows={2} /></div>
              <div className="flex items-center"><input type="checkbox" checked={editForm.is_active} onChange={(e) => setEditForm({...editForm, is_active: e.target.checked})} className="mr-2" /><label>Active</label></div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setShowEditDialog(false)} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded">Cancel</button>
              <button onClick={handleEdit} className="px-4 py-2 bg-emerald-800 text-white rounded hover:bg-emerald-900">Save</button>
            </div>
          </div>
        </div>
      )}

      {showAgentDialog && selectedGroup && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Agent Assignment: {selectedGroup.name}</h2>
            <div className="mb-4">
              <h3 className="font-medium mb-2">Assigned Agent</h3>
              <div className="flex flex-wrap gap-2">
                {selectedGroup.roles.length === 0 ? <span className="text-gray-400 italic">None</span> : selectedGroup.roles.map((r) => (
                  <span key={r.id} className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-purple-100 text-purple-800">
                    {r.name}<button onClick={() => handleRemoveRole(r.id)} className="ml-2">&times;</button>
                  </span>
                ))}
              </div>
            </div>
            <div>
              <h3 className="font-medium mb-2">Available Agents</h3>
              <div className="flex flex-wrap gap-2">
                {allRoles.filter(r => !selectedGroup.roles.some(gr => gr.id === r.id)).map((r) => (
                  <button key={r.id} onClick={() => handleAssignRole(r.id)} className="px-3 py-1 rounded-full text-sm bg-gray-100 hover:bg-gray-200">+ {r.name}</button>
                ))}
              </div>
            </div>
            <div className="flex justify-end mt-6">
              <button onClick={() => setShowAgentDialog(false)} className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300">Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
