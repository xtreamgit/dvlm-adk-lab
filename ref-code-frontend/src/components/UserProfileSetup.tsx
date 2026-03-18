"use client";

import { useState } from 'react';
import { UserProfile } from '../lib/api';

interface UserProfileSetupProps {
  onProfileSubmit: (profile: UserProfile) => void;
  initialProfile?: UserProfile;
  isEditing?: boolean;
  onCancel?: () => void;
}

export default function UserProfileSetup({ onProfileSubmit, initialProfile, isEditing, onCancel }: UserProfileSetupProps) {
  const [name, setName] = useState(initialProfile?.name || '');
  const [preferences, setPreferences] = useState(initialProfile?.preferences || '');
  const [hasChanges, setHasChanges] = useState(false);

  // Track changes when in editing mode
  const checkForChanges = (newName: string, newPreferences: string) => {
    if (!isEditing || !initialProfile) return;
    
    const nameChanged = newName.trim() !== (initialProfile.name || '');
    const preferencesChanged = newPreferences.trim() !== (initialProfile.preferences || '');
    setHasChanges(nameChanged || preferencesChanged);
  };

  const handleNameChange = (value: string) => {
    setName(value);
    checkForChanges(value, preferences);
  };

  const handlePreferencesChange = (value: string) => {
    setPreferences(value);
    checkForChanges(name, value);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim() && (!isEditing || hasChanges)) {
      onProfileSubmit({
        name: name.trim(),
        preferences: preferences.trim() || undefined,
      });
      
      // Reset changes state after successful save in editing mode
      if (isEditing) {
        setHasChanges(false);
      }
    }
  };

  return (
    <div className="max-w-md mx-auto bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
        {isEditing ? 'Edit Profile' : 'Welcome to RAG Agent'}
      </h2>
      <p className="text-gray-600 dark:text-gray-300 mb-6">
        {isEditing 
          ? 'Update your profile information below.'
          : 'Please tell us about yourself to get personalized responses.'
        }
      </p>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Your Name *
          </label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => handleNameChange(e.target.value)}
            placeholder="Enter your name"
            className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            required
          />
        </div>
        
        <div>
          <label htmlFor="preferences" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Preferences (Optional)
          </label>
          <textarea
            id="preferences"
            value={preferences}
            onChange={(e) => handlePreferencesChange(e.target.value)}
            placeholder="Tell us about your interests, preferred communication style, or any specific topics you'd like help with..."
            rows={4}
            className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white resize-none"
          />
        </div>
        
        <div className={`${isEditing ? 'flex gap-3' : ''}`}>
          {isEditing && onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 bg-gray-500 hover:bg-gray-600 text-white font-medium py-3 px-4 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Go Back
            </button>
          )}
          <button
            type="submit"
            disabled={isEditing && !hasChanges}
            className={`${isEditing ? 'flex-1' : 'w-full'} ${
              isEditing && !hasChanges 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-blue-500 hover:bg-blue-600'
            } text-white font-medium py-3 px-4 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50`}
          >
            {isEditing ? 'Save Changes' : 'Start Chatting'}
          </button>
        </div>
      </form>
    </div>
  );
}
