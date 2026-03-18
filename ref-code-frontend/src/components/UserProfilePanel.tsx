"use client";

import { useState, useEffect } from 'react';
import { UserWithProfile, Role, Group, apiClient } from '../lib/api-enhanced';

interface UserProfilePanelProps {
  onProfileUpdate?: () => void;
}

export default function UserProfilePanel({ onProfileUpdate }: UserProfilePanelProps) {
  const [profile, setProfile] = useState<UserWithProfile | null>(null);
  const [roles, setRoles] = useState<Role[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    theme: 'light',
    language: 'en',
    timezone: 'UTC',
  });

  useEffect(() => {
    loadProfileData();
  }, []);

  const loadProfileData = async () => {
    setIsLoading(true);
    try {
      const [profileData, rolesData, groupsData] = await Promise.all([
        apiClient.getMyProfile(),
        apiClient.getMyRoles(),
        apiClient.getMyGroups(),
      ]);

      setProfile(profileData);
      setRoles(rolesData);
      setGroups(groupsData);

      // Set form data from profile
      if (profileData.profile) {
        setFormData({
          theme: profileData.profile.theme || 'light',
          language: profileData.profile.language || 'en',
          timezone: profileData.profile.timezone || 'UTC',
        });
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsLoading(true);
    setError(null);

    try {
      await apiClient.updateProfile(formData);
      await loadProfileData();
      setIsEditing(false);
      if (onProfileUpdate) {
        onProfileUpdate();
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading && !profile) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-800 dark:text-red-200">Failed to load profile</p>
      </div>
    );
  }

  const isAdmin = roles.some(r => r.permissions.includes('*') || r.name === 'system_admin');

  return (
    <div className="space-y-6">
      {/* Profile Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            {profile.full_name}
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">@{profile.username}</p>
          <p className="text-sm text-gray-600 dark:text-gray-400">{profile.email}</p>
        </div>
        
        {isAdmin && (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400">
            Admin
          </span>
        )}
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
          <p className="text-red-800 dark:text-red-200 text-sm">{error}</p>
        </div>
      )}

      {/* Groups */}
      {groups.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Groups</h3>
          <div className="flex flex-wrap gap-2">
            {groups.map((group) => (
              <span
                key={group.id}
                className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400"
              >
                {group.name}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Roles */}
      {roles.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Roles</h3>
          <div className="space-y-2">
            {roles.map((role) => (
              <div
                key={role.id}
                className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-900 dark:text-white">{role.name}</span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {role.permissions.length === 1 && role.permissions[0] === '*'
                      ? 'All permissions'
                      : `${role.permissions.length} permissions`
                    }
                  </span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{role.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Preferences */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Preferences</h3>
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
          >
            {isEditing ? 'Cancel' : 'Edit'}
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Theme
            </label>
            {isEditing ? (
              <select
                value={formData.theme}
                onChange={(e) => setFormData({ ...formData, theme: e.target.value })}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="auto">Auto</option>
              </select>
            ) : (
              <p className="text-sm text-gray-900 dark:text-white capitalize">{formData.theme}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Language
            </label>
            {isEditing ? (
              <select
                value={formData.language}
                onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
              </select>
            ) : (
              <p className="text-sm text-gray-900 dark:text-white">{formData.language}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Timezone
            </label>
            {isEditing ? (
              <select
                value={formData.timezone}
                onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="UTC">UTC</option>
                <option value="America/New_York">Eastern Time</option>
                <option value="America/Chicago">Central Time</option>
                <option value="America/Denver">Mountain Time</option>
                <option value="America/Los_Angeles">Pacific Time</option>
              </select>
            ) : (
              <p className="text-sm text-gray-900 dark:text-white">{formData.timezone}</p>
            )}
          </div>

          {isEditing && (
            <button
              onClick={handleSave}
              disabled={isLoading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Saving...' : 'Save Changes'}
            </button>
          )}
        </div>
      </div>

      {/* Account Info */}
      <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1 pt-4 border-t border-gray-200 dark:border-gray-700">
        <p>Account created: {new Date(profile.created_at).toLocaleDateString()}</p>
        {profile.last_login && (
          <p>Last login: {new Date(profile.last_login).toLocaleDateString()}</p>
        )}
      </div>
    </div>
  );
}
