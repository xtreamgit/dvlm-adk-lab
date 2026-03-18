'use client';

import Link from 'next/link';
import { AlertCircle, Users, Shield, ExternalLink, ArrowRight } from 'lucide-react';

export default function AdminGroupsPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Group Management</h1>
          <p className="text-gray-600">User group and permission management</p>
        </div>

        {/* Deprecation Notice */}
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-6 mb-8">
          <div className="flex items-start">
            <AlertCircle className="h-6 w-6 text-yellow-600 mt-1 mr-3 flex-shrink-0" />
            <div>
              <h2 className="text-lg font-semibold text-yellow-900 mb-2">
                Legacy Group Management Deprecated
              </h2>
              <p className="text-yellow-800 mb-4">
                This page has been deprecated. Group management is now handled through 
                <strong> Google Workspace Groups</strong> and the <strong>Google Groups Bridge</strong>.
              </p>
              <p className="text-yellow-800">
                Manual group creation and user assignments are no longer supported.
              </p>
            </div>
          </div>
        </div>

        {/* New Group Model */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center mb-4">
            <Shield className="h-6 w-6 text-blue-600 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900">Current Group Model</h2>
          </div>
          
          <div className="space-y-4">
            <div className="border-l-4 border-blue-500 pl-4">
              <h3 className="font-semibold text-gray-900 mb-1">Google Workspace Groups</h3>
              <p className="text-gray-600 text-sm">
                Groups are created and managed in Google Workspace. Users are added to groups through 
                the Google Admin Console.
              </p>
            </div>

            <div className="border-l-4 border-green-500 pl-4">
              <h3 className="font-semibold text-gray-900 mb-1">Google Groups Bridge</h3>
              <p className="text-gray-600 text-sm">
                The bridge automatically syncs Google Groups and maps them to chatbot groups, 
                granting appropriate access to agents and corpora.
              </p>
            </div>

            <div className="border-l-4 border-purple-500 pl-4">
              <h3 className="font-semibold text-gray-900 mb-1">Automatic Synchronization</h3>
              <p className="text-gray-600 text-sm">
                Group memberships are automatically synchronized from Google Workspace. 
                No manual assignment required.
              </p>
            </div>
          </div>
        </div>

        {/* How to Manage Groups */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center mb-4">
            <Users className="h-6 w-6 text-blue-600 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900">How to Manage Groups</h2>
          </div>

          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-2">1. Create Groups in Google Workspace</h3>
              <p className="text-gray-600 text-sm mb-2">
                Create groups in your Google Workspace organization and add users to them.
              </p>
              <a
                href="https://admin.google.com/ac/groups"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm"
              >
                Open Google Groups Console
                <ExternalLink className="h-4 w-4 ml-1" />
              </a>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-2">2. Configure Google Groups Bridge</h3>
              <p className="text-gray-600 text-sm mb-2">
                Map Google Groups to chatbot groups and configure agent/corpus access permissions.
              </p>
              <Link
                href="/admin/google-groups"
                className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm"
              >
                Go to Google Groups Bridge
                <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-2">3. Verify Synchronization</h3>
              <p className="text-gray-600 text-sm mb-2">
                Check that Google Groups are properly synced and users have correct access.
              </p>
              <Link
                href="/admin/chatbot-groups"
                className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm"
              >
                View Chatbot Groups
                <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </div>
          </div>
        </div>

        {/* Example Groups */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Common Group Examples</h2>
          <div className="space-y-3">
            <div className="flex items-start p-3 bg-gray-50 rounded-lg">
              <div className="flex-1">
                <div className="font-medium text-gray-900">admin-users@yourdomain.com</div>
                <div className="text-sm text-gray-600">Administrators with full system access</div>
              </div>
            </div>
            <div className="flex items-start p-3 bg-gray-50 rounded-lg">
              <div className="flex-1">
                <div className="font-medium text-gray-900">rag-viewers@yourdomain.com</div>
                <div className="text-sm text-gray-600">Users with read-only access to RAG corpora</div>
              </div>
            </div>
            <div className="flex items-start p-3 bg-gray-50 rounded-lg">
              <div className="flex-1">
                <div className="font-medium text-gray-900">corpus-managers@yourdomain.com</div>
                <div className="text-sm text-gray-600">Users who can manage corpus content</div>
              </div>
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
              href="/admin/chatbot-groups"
              className="flex items-center justify-between p-3 bg-white rounded-lg hover:shadow-md transition-shadow"
            >
              <span className="text-gray-900">Chatbot Groups</span>
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
              href="/admin/corpora"
              className="flex items-center justify-between p-3 bg-white rounded-lg hover:shadow-md transition-shadow"
            >
              <span className="text-gray-900">Corpus Management</span>
              <ArrowRight className="h-4 w-4 text-gray-400" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
