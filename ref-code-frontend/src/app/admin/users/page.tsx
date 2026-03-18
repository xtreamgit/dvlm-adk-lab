'use client';

import Link from 'next/link';
import { AlertCircle, Users, Shield, ExternalLink, ArrowRight } from 'lucide-react';

export default function AdminUsersPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">User Management</h1>
          <p className="text-gray-600">Authentication and user access control</p>
        </div>

        {/* Deprecation Notice */}
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-6 mb-8">
          <div className="flex items-start">
            <AlertCircle className="h-6 w-6 text-yellow-600 mt-1 mr-3 flex-shrink-0" />
            <div>
              <h2 className="text-lg font-semibold text-yellow-900 mb-2">
                Legacy User Management Deprecated
              </h2>
              <p className="text-yellow-800 mb-4">
                This page has been deprecated. User authentication and authorization are now managed 
                through <strong>Google Identity-Aware Proxy (IAP)</strong> and <strong>Google Groups</strong>.
              </p>
              <p className="text-yellow-800">
                Manual user creation, password management, and group assignments are no longer supported.
              </p>
            </div>
          </div>
        </div>

        {/* New Authentication Model */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center mb-4">
            <Shield className="h-6 w-6 text-blue-600 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900">Current Authentication Model</h2>
          </div>
          
          <div className="space-y-4">
            <div className="border-l-4 border-blue-500 pl-4">
              <h3 className="font-semibold text-gray-900 mb-1">Authentication: Google IAP</h3>
              <p className="text-gray-600 text-sm">
                Users authenticate via Google Cloud Identity-Aware Proxy using their Google Workspace accounts.
                No passwords are stored in the application.
              </p>
            </div>

            <div className="border-l-4 border-green-500 pl-4">
              <h3 className="font-semibold text-gray-900 mb-1">Authorization: Google Groups</h3>
              <p className="text-gray-600 text-sm">
                User permissions and access control are managed through Google Workspace Groups.
                The Google Groups Bridge automatically syncs group memberships.
              </p>
            </div>

            <div className="border-l-4 border-purple-500 pl-4">
              <h3 className="font-semibold text-gray-900 mb-1">User Provisioning</h3>
              <p className="text-gray-600 text-sm">
                Users are automatically created on first login via IAP. No manual user creation required.
              </p>
            </div>
          </div>
        </div>

        {/* How to Manage Users */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center mb-4">
            <Users className="h-6 w-6 text-blue-600 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900">How to Manage Users</h2>
          </div>

          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-2">1. Add Users to Google Workspace</h3>
              <p className="text-gray-600 text-sm mb-2">
                Create user accounts in your Google Workspace organization.
              </p>
              <a
                href="https://admin.google.com/ac/users"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm"
              >
                Open Google Admin Console
                <ExternalLink className="h-4 w-4 ml-1" />
              </a>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-2">2. Assign Users to Google Groups</h3>
              <p className="text-gray-600 text-sm mb-2">
                Add users to appropriate Google Groups to grant them access to agents and corpora.
              </p>
              <a
                href="https://admin.google.com/ac/groups"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm"
              >
                Manage Google Groups
                <ExternalLink className="h-4 w-4 ml-1" />
              </a>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-2">3. Configure Google Groups Bridge</h3>
              <p className="text-gray-600 text-sm mb-2">
                Map Google Groups to chatbot groups and manage corpus access permissions.
              </p>
              <Link
                href="/admin/google-groups"
                className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm"
              >
                Go to Google Groups Bridge
                <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </div>
          </div>
        </div>

        {/* Quick Links */}
        <div className="bg-blue-50 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Related Admin Pages</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Link
              href="/admin/google-groups"
              className="flex items-center justify-between p-3 bg-white rounded-lg hover:shadow-md transition-shadow"
            >
              <span className="text-gray-900">Google Groups Bridge</span>
              <ArrowRight className="h-4 w-4 text-gray-400" />
            </Link>
            <Link
              href="/admin/chatbot-users"
              className="flex items-center justify-between p-3 bg-white rounded-lg hover:shadow-md transition-shadow"
            >
              <span className="text-gray-900">Chatbot Users</span>
              <ArrowRight className="h-4 w-4 text-gray-400" />
            </Link>
            <Link
              href="/admin/chatbot-groups"
              className="flex items-center justify-between p-3 bg-white rounded-lg hover:shadow-md transition-shadow"
            >
              <span className="text-gray-900">Chatbot Groups</span>
              <ArrowRight className="h-4 w-4 text-gray-400" />
            </Link>
            <Link
              href="/admin/audit"
              className="flex items-center justify-between p-3 bg-white rounded-lg hover:shadow-md transition-shadow"
            >
              <span className="text-gray-900">Audit Logs</span>
              <ArrowRight className="h-4 w-4 text-gray-400" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
