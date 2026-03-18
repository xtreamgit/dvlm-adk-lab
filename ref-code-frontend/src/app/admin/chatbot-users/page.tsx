'use client';

import { useState, useEffect } from 'react';
import { getAuthHeaders, getAuthHeadersOnly } from '../../../lib/auth-headers';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || '';

interface ChatbotGroup {
  id: number;
  name: string;
  description?: string;
}

interface ChatbotUser {
  id: number;
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login: string | null;
  notes: string | null;
  groups: ChatbotGroup[];
}

export default function ChatbotUsersPage() {
  const [users, setUsers] = useState<ChatbotUser[]>([]);
  const [allGroups, setAllGroups] = useState<ChatbotGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showGroupDialog, setShowGroupDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState<ChatbotUser | null>(null);
  const [sortField, setSortField] = useState<'username' | 'full_name' | null>(null);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [selectedUserIds, setSelectedUserIds] = useState<Set<number>>(new Set());
  const [createForm, setCreateForm] = useState({
    username: '',
    email: '',
    full_name: '',
    password: '',
    notes: '',
    addToDefaultGroup: true,
  });
  const [editForm, setEditForm] = useState({
    email: '',
    full_name: '',
    is_active: true,
    password: '',
    notes: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [usersData, groupsData] = await Promise.all([
        fetchChatbotUsers(),
        fetchChatbotGroups(),
      ]);
      setUsers(usersData);
      setAllGroups(groupsData);
      return usersData;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
      return [];
    } finally {
      setLoading(false);
    }
  };

  const fetchChatbotUsers = async () => {
    const response = await fetch(`${BACKEND_URL}/api/admin/chatbot/users`, {
      headers: getAuthHeadersOnly(),
    });
    if (!response.ok) throw new Error('Failed to fetch chatbot users');
    return response.json();
  };

  const fetchChatbotGroups = async () => {
    const response = await fetch(`${BACKEND_URL}/api/admin/chatbot/groups`, {
      headers: getAuthHeadersOnly(),
    });
    if (!response.ok) throw new Error('Failed to fetch chatbot groups');
    return response.json();
  };

  const handleCreateUser = async () => {
    if (!createForm.username || !createForm.email || !createForm.full_name) {
      alert('Please fill in all required fields');
      return;
    }

    try {
      // Create user
      const response = await fetch(`${BACKEND_URL}/api/admin/chatbot/users`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          username: createForm.username,
          email: createForm.email,
          full_name: createForm.full_name,
          password: createForm.password,
          notes: createForm.notes,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create user');
      }

      const newUser = await response.json();

      // Add to default-chatbot-users group if checkbox is checked
      if (createForm.addToDefaultGroup) {
        const defaultGroup = allGroups.find(g => g.name === 'default-chatbot-users');
        if (defaultGroup) {
          await fetch(`${BACKEND_URL}/api/admin/chatbot/users/${newUser.id}/groups/${defaultGroup.id}`, {
            method: 'POST',
            headers: getAuthHeadersOnly(),
          });
        }
      }

      setShowCreateDialog(false);
      setCreateForm({ username: '', email: '', full_name: '', password: '', notes: '', addToDefaultGroup: true });
      await loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create user');
    }
  };

  const handleEditUser = async () => {
    if (!selectedUser) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/chatbot/users/${selectedUser.id}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(editForm),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update user');
      }

      setShowEditDialog(false);
      setSelectedUser(null);
      await loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update user');
    }
  };

  const handleDeactivateUser = async (userId: number) => {
    if (!confirm('Are you sure you want to deactivate this user?')) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/chatbot/users/${userId}`, {
        method: 'DELETE',
        headers: getAuthHeadersOnly(),
      });

      if (!response.ok) throw new Error('Failed to deactivate user');
      await loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to deactivate user');
    }
  };

  const handlePermanentDeleteUser = async (userId: number, username: string) => {
    const confirmed = prompt(
      `This will PERMANENTLY delete user "${username}" and all their group memberships.\n\nThis action cannot be undone.\n\nType the username to confirm:`
    );
    if (confirmed !== username) {
      if (confirmed !== null) alert('Username did not match. Deletion cancelled.');
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/chatbot/users/${userId}/permanent`, {
        method: 'DELETE',
        headers: getAuthHeadersOnly(),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete user');
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete user');
    } finally {
      setSelectedUserIds(new Set());
      await loadData();
    }
  };

  const handleBulkDelete = async () => {
    const selectedUsers = users.filter(u => selectedUserIds.has(u.id));
    const activeSelected = selectedUsers.filter(u => u.is_active);
    const inactiveSelected = selectedUsers.filter(u => !u.is_active);

    if (inactiveSelected.length === 0) {
      alert('No inactive users selected. Only inactive users can be deleted.');
      return;
    }

    if (activeSelected.length > 0) {
      alert(`${activeSelected.length} active user(s) will be skipped. Only ${inactiveSelected.length} inactive user(s) will be deleted.`);
    }

    const names = inactiveSelected.map(u => u.username).join(', ');
    if (!confirm(`Permanently delete ${inactiveSelected.length} user(s)?\n\n${names}\n\nThis action cannot be undone.`)) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/chatbot/users/bulk-delete`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ user_ids: inactiveSelected.map(u => u.id) }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete users');
      }

      const result = await response.json();
      alert(result.message);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete users');
    } finally {
      setSelectedUserIds(new Set());
      await loadData();
    }
  };

  const toggleSelectUser = (userId: number) => {
    setSelectedUserIds(prev => {
      const next = new Set(prev);
      if (next.has(userId)) next.delete(userId);
      else next.add(userId);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selectedUserIds.size === users.length) {
      setSelectedUserIds(new Set());
    } else {
      setSelectedUserIds(new Set(users.map(u => u.id)));
    }
  };

  const handleAssignGroup = async (groupId: number) => {
    if (!selectedUser) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/chatbot/users/${selectedUser.id}/groups/${groupId}`, {
        method: 'POST',
        headers: getAuthHeadersOnly(),
      });

      if (!response.ok) throw new Error('Failed to assign group');
      
      // Refresh data without triggering loading state
      const [usersData] = await Promise.all([
        fetchChatbotUsers(),
      ]);
      setUsers(usersData);
      const updatedUser = usersData.find((u: ChatbotUser) => u.id === selectedUser.id);
      if (updatedUser) setSelectedUser(updatedUser);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to assign group');
    }
  };

  const handleRemoveGroup = async (groupId: number) => {
    if (!selectedUser) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/chatbot/users/${selectedUser.id}/groups/${groupId}`, {
        method: 'DELETE',
        headers: getAuthHeadersOnly(),
      });

      if (!response.ok) throw new Error('Failed to remove group');
      
      // Refresh data without triggering loading state
      const [usersData] = await Promise.all([
        fetchChatbotUsers(),
      ]);
      setUsers(usersData);
      const updatedUser = usersData.find((u: ChatbotUser) => u.id === selectedUser.id);
      if (updatedUser) setSelectedUser(updatedUser);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to remove group');
    }
  };

  const openEditDialog = (user: ChatbotUser) => {
    setSelectedUser(user);
    setEditForm({
      email: user.email,
      full_name: user.full_name,
      is_active: user.is_active,
      password: '',
      notes: user.notes || '',
    });
    setShowEditDialog(true);
  };

  const openGroupDialog = (user: ChatbotUser) => {
    setSelectedUser(user);
    setShowGroupDialog(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading chatbot users...</p>
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
          <button onClick={loadData} className="bg-emerald-800 text-white px-4 py-2 rounded hover:bg-emerald-900">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Chatbot Users</h1>
          <p className="text-gray-600">Manage users who can access the chatbot</p>
        </div>
        <button
          onClick={() => setShowCreateDialog(true)}
          className="bg-emerald-800 text-white px-4 py-2 rounded-lg hover:bg-emerald-900 flex items-center gap-2"
        >
          <span>+</span> Create User
        </button>
      </div>

      {selectedUserIds.size > 0 && (
        <div className="mb-4 flex items-center gap-4 bg-blue-50 border border-blue-200 rounded-lg px-4 py-3">
          <span className="text-sm font-medium text-blue-800">
            {selectedUserIds.size} user{selectedUserIds.size !== 1 ? 's' : ''} selected
          </span>
          <button
            onClick={handleBulkDelete}
            className="px-3 py-1.5 bg-red-600 text-white text-sm font-semibold rounded hover:bg-red-700 transition-colors"
          >
            Delete Selected
          </button>
          <button
            onClick={() => setSelectedUserIds(new Set())}
            className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-colors"
          >
            Clear Selection
          </button>
        </div>
      )}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left">
                <input
                  type="checkbox"
                  checked={users.length > 0 && selectedUserIds.size === users.length}
                  onChange={toggleSelectAll}
                  className="h-4 w-4 text-blue-600 rounded border-gray-300 cursor-pointer"
                />
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100 select-none"
                onClick={() => {
                  if (sortField === 'username') {
                    setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                  } else {
                    setSortField('username');
                    setSortOrder('asc');
                  }
                }}
              >
                Username {sortField === 'username' ? (sortOrder === 'asc' ? '↑' : '↓') : '↕'}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100 select-none"
                onClick={() => {
                  if (sortField === 'full_name') {
                    setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                  } else {
                    setSortField('full_name');
                    setSortOrder('asc');
                  }
                }}
              >
                Full Name {sortField === 'full_name' ? (sortOrder === 'asc' ? '↑' : '↓') : '↕'}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Groups</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {users.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                  No chatbot users yet. Click &quot;Create User&quot; to add one.
                </td>
              </tr>
            ) : (
              [...users].sort((a, b) => {
                  if (!sortField) return 0;
                  const aVal = sortField === 'username' ? a.username : a.full_name;
                  const bVal = sortField === 'username' ? b.username : b.full_name;
                  return sortOrder === 'asc' 
                    ? aVal.localeCompare(bVal)
                    : bVal.localeCompare(aVal);
                }).map((user) => (
                <tr key={user.id} className={`hover:bg-gray-300 ${selectedUserIds.has(user.id) ? 'bg-blue-50' : 'even:bg-gray-200'}`}>
                  <td className="px-4 py-4">
                    <input
                      type="checkbox"
                      checked={selectedUserIds.has(user.id)}
                      onChange={() => toggleSelectUser(user.id)}
                      className="h-4 w-4 text-blue-600 rounded border-gray-300 cursor-pointer"
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-base font-semibold" style={{ color: 'rgb(0,84,64)' }}>{user.username}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{user.email}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">{user.full_name}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    <div className="flex flex-wrap gap-1">
                      {user.groups.map((g) => (
                        <span key={g.id} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                          {g.name}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onClick={() => openGroupDialog(user)} className="text-amber-600 hover:text-amber-800 mr-3">Groups</button>
                    <button onClick={() => openEditDialog(user)} className="text-slate-600 hover:text-slate-800 mr-3">Edit</button>
                    {user.is_active ? (
                      <button onClick={() => handleDeactivateUser(user.id)} className="text-rose-600 hover:text-rose-800">Deactivate</button>
                    ) : (
                      <button onClick={() => handlePermanentDeleteUser(user.id, user.username)} className="text-red-700 hover:text-red-900 font-semibold">Delete</button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create Dialog */}
      {showCreateDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Create Chatbot User</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Username *</label>
                <input
                  type="text"
                  value={createForm.username}
                  onChange={(e) => setCreateForm({ ...createForm, username: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                <input
                  type="email"
                  value={createForm.email}
                  onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
                <input
                  type="text"
                  value={createForm.full_name}
                  onChange={(e) => setCreateForm({ ...createForm, full_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input
                  type="password"
                  value={createForm.password}
                  onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  value={createForm.notes}
                  onChange={(e) => setCreateForm({ ...createForm, notes: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  rows={2}
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="addToDefaultGroup"
                  checked={createForm.addToDefaultGroup}
                  onChange={(e) => setCreateForm({ ...createForm, addToDefaultGroup: e.target.checked })}
                  className="mr-2 h-4 w-4 text-blue-600 rounded"
                />
                <label htmlFor="addToDefaultGroup" className="text-sm font-bold text-gray-700">
                  Add to default-chatbot-users group
                </label>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setShowCreateDialog(false)} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded">Cancel</button>
              <button onClick={handleCreateUser} className="px-4 py-2 bg-emerald-800 text-white rounded hover:bg-emerald-900">Create</button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Dialog */}
      {showEditDialog && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Edit User: {selectedUser.username}</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                <input
                  type="text"
                  value={editForm.full_name}
                  onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">New Password (leave blank to keep)</label>
                <input
                  type="password"
                  value={editForm.password}
                  onChange={(e) => setEditForm({ ...editForm, password: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={editForm.is_active}
                  onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })}
                  className="mr-2"
                />
                <label className="text-sm text-gray-700">Active</label>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setShowEditDialog(false)} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded">Cancel</button>
              <button onClick={handleEditUser} className="px-4 py-2 bg-emerald-800 text-white rounded hover:bg-emerald-900">Save</button>
            </div>
          </div>
        </div>
      )}

      {/* Group Assignment Dialog */}
      {showGroupDialog && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Manage Groups: {selectedUser.username}</h2>
            <div className="mb-4">
              <h3 className="font-medium text-gray-700 mb-2">Current Groups</h3>
              <div className="flex flex-wrap gap-2">
                {selectedUser.groups.length === 0 ? (
                  <span className="text-gray-400 italic">No groups assigned</span>
                ) : (
                  selectedUser.groups.map((g) => (
                    <span key={g.id} className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800">
                      {g.name}
                      <button onClick={() => handleRemoveGroup(g.id)} className="ml-2 text-blue-600 hover:text-blue-900">&times;</button>
                    </span>
                  ))
                )}
              </div>
            </div>
            <div>
              <h3 className="font-medium text-gray-700 mb-2">Available Groups</h3>
              <div className="flex flex-wrap gap-2">
                {allGroups.filter(g => !selectedUser.groups.some(ug => ug.id === g.id)).map((g) => (
                  <button
                    key={g.id}
                    onClick={() => handleAssignGroup(g.id)}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-800 hover:bg-gray-200"
                  >
                    + {g.name}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex justify-end mt-6">
              <button onClick={() => setShowGroupDialog(false)} className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300">Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
