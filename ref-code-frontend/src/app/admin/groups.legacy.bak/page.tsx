'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-enhanced';

interface Role {
  id: number;
  name: string;
  permissions: string[];
  created_at: string;
}

interface Group {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  roles?: Role[];
}

export default function AdminGroupsPage() {
  const [groups, setGroups] = useState<Group[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateGroupDialog, setShowCreateGroupDialog] = useState(false);
  const [showEditGroupDialog, setShowEditGroupDialog] = useState(false);
  const [showCreateRoleDialog, setShowCreateRoleDialog] = useState(false);
  const [showRoleDialog, setShowRoleDialog] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null);
  const [createGroupForm, setCreateGroupForm] = useState({
    name: '',
    description: '',
  });
  const [editGroupForm, setEditGroupForm] = useState({
    name: '',
    description: '',
  });
  const [createRoleForm, setCreateRoleForm] = useState({
    name: '',
    permissions: [] as string[],
  });

  const availablePermissions = [
    'manage:users',
    'manage:groups',
    'manage:roles',
    'manage:corpora',
    'view:audit_logs',
    'admin:all',
  ];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [groupsData, rolesData] = await Promise.all([
        apiClient.getAllGroups(),
        apiClient.getAllRoles(),
      ]);
      setGroups(groupsData);
      setRoles(rolesData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage);
      console.error('Load data error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGroup = async () => {
    if (!createGroupForm.name) {
      alert('Please enter a group name');
      return;
    }

    try {
      await apiClient.createGroup(createGroupForm);
      setShowCreateGroupDialog(false);
      setCreateGroupForm({ name: '', description: '' });
      await loadData();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      console.error('Create group error:', err);
      alert(`Failed to create group: ${errorMessage}`);
    }
  };

  const handleEditGroup = async () => {
    if (!selectedGroup) return;

    try {
      const updates: any = {};
      if (editGroupForm.name && editGroupForm.name !== selectedGroup.name) {
        updates.name = editGroupForm.name;
      }
      if (editGroupForm.description !== selectedGroup.description) {
        updates.description = editGroupForm.description;
      }

      if (Object.keys(updates).length > 0) {
        await apiClient.updateGroup(selectedGroup.id, updates);
      }

      setShowEditGroupDialog(false);
      setSelectedGroup(null);
      await loadData();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      console.error('Update group error:', err);
      alert(`Failed to update group: ${errorMessage}`);
    }
  };

  const handleDeleteGroup = async (groupId: number, groupName: string) => {
    if (!confirm(`Are you sure you want to delete group "${groupName}"?`)) {
      return;
    }

    try {
      await apiClient.deleteGroup(groupId);
      await loadData();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      console.error('Delete group error:', err);
      alert(`Failed to delete group: ${errorMessage}`);
    }
  };

  const handleCreateRole = async () => {
    if (!createRoleForm.name || createRoleForm.permissions.length === 0) {
      alert('Please enter a role name and select at least one permission');
      return;
    }

    try {
      await apiClient.createRole(createRoleForm);
      setShowCreateRoleDialog(false);
      setCreateRoleForm({ name: '', permissions: [] });
      await loadData();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      console.error('Create role error:', err);
      alert(`Failed to create role: ${errorMessage}`);
    }
  };

  const handleAssignRole = async (roleId: number) => {
    if (!selectedGroup) return;

    try {
      await apiClient.assignRoleToGroup(selectedGroup.id, roleId);
      await loadData();
      const updatedGroup = groups.find(g => g.id === selectedGroup.id);
      if (updatedGroup) {
        setSelectedGroup(updatedGroup);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      console.error('Assign role error:', err);
      alert(`Failed to assign role: ${errorMessage}`);
    }
  };

  const handleRemoveRole = async (roleId: number) => {
    if (!selectedGroup) return;

    if (!confirm('Remove this role from the group?')) {
      return;
    }

    try {
      await apiClient.removeRoleFromGroup(selectedGroup.id, roleId);
      await loadData();
      const updatedGroup = groups.find(g => g.id === selectedGroup.id);
      if (updatedGroup) {
        setSelectedGroup(updatedGroup);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      console.error('Remove role error:', err);
      alert(`Failed to remove role: ${errorMessage}`);
    }
  };

  const openEditDialog = (group: Group) => {
    setSelectedGroup(group);
    setEditGroupForm({
      name: group.name,
      description: group.description || '',
    });
    setShowEditGroupDialog(true);
  };

  const openRoleDialog = (group: Group) => {
    setSelectedGroup(group);
    setShowRoleDialog(true);
  };

  const togglePermission = (permission: string) => {
    setCreateRoleForm(prev => ({
      ...prev,
      permissions: prev.permissions.includes(permission)
        ? prev.permissions.filter(p => p !== permission)
        : [...prev.permissions, permission],
    }));
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading groups...</p>
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
            onClick={loadData}
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
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Group Management</h1>
          <p className="text-gray-600">Manage groups and role assignments</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowCreateRoleDialog(true)}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
          >
            + Create Role
          </button>
          <button
            onClick={() => setShowCreateGroupDialog(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            + Create Group
          </button>
        </div>
      </div>

      {/* Groups Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden mb-8">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Groups</h2>
        </div>
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Description
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {groups.map((group) => (
              <tr key={group.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {group.name}
                </td>
                <td className="px-6 py-4 text-sm text-gray-900">
                  {group.description || <span className="text-gray-400 italic">No description</span>}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(group.created_at)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    onClick={() => openRoleDialog(group)}
                    className="text-purple-600 hover:text-purple-900 mr-3"
                  >
                    Roles
                  </button>
                  <button
                    onClick={() => openEditDialog(group)}
                    className="text-indigo-600 hover:text-indigo-900 mr-3"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDeleteGroup(group.id, group.name)}
                    className="text-red-600 hover:text-red-900"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Roles Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Roles</h2>
        </div>
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Permissions
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {roles.map((role) => (
              <tr key={role.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {role.name}
                </td>
                <td className="px-6 py-4 text-sm text-gray-900">
                  <div className="flex flex-wrap gap-1">
                    {role.permissions && role.permissions.length > 0 ? (
                      role.permissions.map((perm, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800"
                        >
                          {perm}
                        </span>
                      ))
                    ) : (
                      <span className="text-gray-400 italic">No permissions</span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(role.created_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create Group Dialog */}
      {showCreateGroupDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Create New Group</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name *
                </label>
                <input
                  type="text"
                  value={createGroupForm.name}
                  onChange={(e) => setCreateGroupForm({ ...createGroupForm, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={createGroupForm.description}
                  onChange={(e) => setCreateGroupForm({ ...createGroupForm, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  rows={3}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowCreateGroupDialog(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateGroup}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Create Group
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Group Dialog */}
      {showEditGroupDialog && selectedGroup && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Edit Group: {selectedGroup.name}</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={editGroupForm.name}
                  onChange={(e) => setEditGroupForm({ ...editGroupForm, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={editGroupForm.description}
                  onChange={(e) => setEditGroupForm({ ...editGroupForm, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  rows={3}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowEditGroupDialog(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleEditGroup}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Role Dialog */}
      {showCreateRoleDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Create New Role</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name *
                </label>
                <input
                  type="text"
                  value={createRoleForm.name}
                  onChange={(e) => setCreateRoleForm({ ...createRoleForm, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Permissions *
                </label>
                <div className="space-y-2">
                  {availablePermissions.map((perm) => (
                    <label key={perm} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={createRoleForm.permissions.includes(perm)}
                        onChange={() => togglePermission(perm)}
                        className="mr-2"
                      />
                      <span className="text-sm">{perm}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowCreateRoleDialog(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateRole}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                Create Role
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Role Management Dialog */}
      {showRoleDialog && selectedGroup && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl my-8">
            <h2 className="text-xl font-bold mb-4">
              Manage Roles: {selectedGroup.name}
            </h2>
            
            <div className="grid grid-cols-2 gap-6">
              {/* Current Roles */}
              <div>
                <h3 className="font-semibold mb-3 text-gray-700">Current Roles</h3>
                <div className="space-y-3">
                  {selectedGroup.roles && selectedGroup.roles.length > 0 ? (
                    selectedGroup.roles.map((role) => (
                      <div
                        key={role.id}
                        className="p-3 bg-gray-50 rounded-lg border border-gray-200"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="font-semibold text-gray-900">{role.name}</div>
                            <div className="text-xs text-gray-500 mt-1">
                              {role.permissions.length} permission{role.permissions.length !== 1 ? 's' : ''}
                            </div>
                          </div>
                          <button
                            onClick={() => handleRemoveRole(role.id)}
                            className="text-red-600 hover:text-red-800 text-sm font-medium ml-2"
                          >
                            Remove
                          </button>
                        </div>
                        {role.permissions && role.permissions.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {role.permissions.slice(0, 3).map((perm, idx) => (
                              <span
                                key={idx}
                                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800"
                              >
                                {perm}
                              </span>
                            ))}
                            {role.permissions.length > 3 && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-200 text-gray-600">
                                +{role.permissions.length - 3} more
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-400 italic">No roles assigned</p>
                  )}
                </div>
              </div>

              {/* Available Roles */}
              <div>
                <h3 className="font-semibold mb-3 text-gray-700">Available Roles</h3>
                <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                  {roles
                    .filter((r) => !selectedGroup.roles?.find((gr) => gr.id === r.id))
                    .map((role) => (
                      <div
                        key={role.id}
                        className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-blue-300 transition-colors"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="font-semibold text-gray-900">{role.name}</div>
                            <div className="text-xs text-gray-500 mt-1">
                              {role.permissions.length} permission{role.permissions.length !== 1 ? 's' : ''}
                            </div>
                          </div>
                          <button
                            onClick={() => handleAssignRole(role.id)}
                            className="text-blue-600 hover:text-blue-800 text-sm font-medium ml-2 px-3 py-1 rounded border border-blue-600 hover:bg-blue-50"
                          >
                            Assign
                          </button>
                        </div>
                        {role.permissions && role.permissions.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {role.permissions.slice(0, 4).map((perm, idx) => (
                              <span
                                key={idx}
                                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                              >
                                {perm}
                              </span>
                            ))}
                            {role.permissions.length > 4 && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-200 text-gray-600">
                                +{role.permissions.length - 4} more
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  {roles.filter((r) => !selectedGroup.roles?.find((gr) => gr.id === r.id))
                    .length === 0 && (
                    <p className="text-gray-400 italic">All roles assigned</p>
                  )}
                </div>
              </div>
            </div>

            <div className="flex justify-end mt-6">
              <button
                onClick={() => setShowRoleDialog(false)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
