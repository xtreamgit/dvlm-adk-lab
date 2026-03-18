'use client';

import { AlertCircle, Users, Settings } from 'lucide-react';
import Link from 'next/link';

export default function AgentAssignmentsDeprecated() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
          <div className="flex items-center gap-4 mb-4">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <AlertCircle className="w-8 h-8 text-yellow-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Agent Assignments</h1>
              <p className="text-gray-600 mt-1">Legacy Feature - Deprecated</p>
            </div>
          </div>
          
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mt-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <AlertCircle className="h-5 w-5 text-yellow-400" />
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">
                  This page has been deprecated
                </h3>
                <div className="mt-2 text-sm text-yellow-700">
                  <p>
                    Agent assignments are now managed through the <strong>Chatbot Users</strong> system,
                    which integrates with Google Groups Bridge for authorization.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Migration Guide */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Settings className="w-6 h-6 text-blue-600" />
            How Agent Assignment Works Now
          </h2>
          
          <div className="space-y-6">
            <div className="border-l-4 border-blue-500 pl-4">
              <h3 className="font-semibold text-gray-900 mb-2">1. Chatbot Users & Groups</h3>
              <p className="text-gray-700 mb-2">
                Users are assigned to chatbot groups (admin-group, content-manager-group, etc.) 
                through the Google Groups Bridge, which syncs with Google Workspace Groups.
              </p>
              <Link 
                href="/admin/chatbot-users" 
                className="text-blue-600 hover:text-blue-800 underline inline-flex items-center gap-1"
              >
                Manage Chatbot Users →
              </Link>
            </div>

            <div className="border-l-4 border-green-500 pl-4">
              <h3 className="font-semibold text-gray-900 mb-2">2. Agent Types per Group</h3>
              <p className="text-gray-700 mb-2">
                Each chatbot group is assigned specific agent types (e.g., admin-group gets admin_agent).
                This is configured in the chatbot permissions system.
              </p>
              <Link 
                href="/admin/chatbot-permissions" 
                className="text-blue-600 hover:text-blue-800 underline inline-flex items-center gap-1"
              >
                Configure Agent Permissions →
              </Link>
            </div>

            <div className="border-l-4 border-purple-500 pl-4">
              <h3 className="font-semibold text-gray-900 mb-2">3. Google Groups Bridge</h3>
              <p className="text-gray-700 mb-2">
                The Google Groups Bridge automatically syncs user memberships from Google Workspace,
                determining which chatbot group (and thus which agent) each user gets.
              </p>
              <Link 
                href="/admin/google-groups" 
                className="text-blue-600 hover:text-blue-800 underline inline-flex items-center gap-1"
              >
                View Google Groups Mapping →
              </Link>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Users className="w-6 h-6 text-blue-600" />
            Quick Actions
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Link
              href="/admin/chatbot-users"
              className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all"
            >
              <h3 className="font-semibold text-gray-900 mb-1">View Chatbot Users</h3>
              <p className="text-sm text-gray-600">
                See all chatbot users and their group assignments
              </p>
            </Link>

            <Link
              href="/admin/chatbot-groups"
              className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all"
            >
              <h3 className="font-semibold text-gray-900 mb-1">Manage Chatbot Groups</h3>
              <p className="text-sm text-gray-600">
                Configure chatbot groups and their priorities
              </p>
            </Link>

            <Link
              href="/admin/chatbot-permissions"
              className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all"
            >
              <h3 className="font-semibold text-gray-900 mb-1">Agent Permissions</h3>
              <p className="text-sm text-gray-600">
                Assign agent types to chatbot groups
              </p>
            </Link>

            <Link
              href="/admin/google-groups"
              className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all"
            >
              <h3 className="font-semibold text-gray-900 mb-1">Google Groups Bridge</h3>
              <p className="text-sm text-gray-600">
                View Google Workspace group mappings
              </p>
            </Link>
          </div>
        </div>

        {/* Back Link */}
        <div className="mt-6 text-center">
          <Link 
            href="/admin" 
            className="text-blue-600 hover:text-blue-800 underline"
          >
            ← Back to Admin Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
