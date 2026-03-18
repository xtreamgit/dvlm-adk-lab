/**
 * Agent Permissions Hook
 * 
 * Provides access to the current user's agent type and tool permissions.
 * Fetches permissions from the backend and caches them.
 */

import { useState, useEffect } from 'react';
import { getAuthHeadersOnly } from '../lib/auth-headers';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || '';

export interface AgentPermissions {
  agentType: string | null;
  allowedTools: string[];
  toolCount: number;
}

export interface AgentTypeInfo {
  type: string;
  display_name: string;
  description: string;
  use_case: string;
  color: string;
  tools: string[];
  incremental_tools: string[];
}

/**
 * Hook to get current user's agent permissions
 */
export function useAgentPermissions() {
  const [permissions, setPermissions] = useState<AgentPermissions | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPermissions();
  }, []);

  const fetchPermissions = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/admin/chatbot/my-agent-type`, {
        headers: getAuthHeadersOnly()
      });

      if (!response.ok) {
        throw new Error('Failed to fetch permissions');
      }

      const data = await response.json();
      setPermissions({
        agentType: data.agent_type,
        allowedTools: data.allowed_tools || [],
        toolCount: data.tool_count || 0
      });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load permissions');
      setPermissions(null);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Check if user has access to a specific tool
   */
  const canUseTool = (toolName: string): boolean => {
    if (!permissions) return false;
    return permissions.allowedTools.includes(toolName);
  };

  /**
   * Check if user has a specific agent type or higher
   */
  const hasAgentTypeLevel = (requiredType: string): boolean => {
    if (!permissions?.agentType) return false;

    const agentTypeLevels: Record<string, number> = {
      'viewer': 1,
      'contributor': 2,
      'content-manager': 3,
      'corpus-manager': 4
    };

    const userLevel = agentTypeLevels[permissions.agentType] || 0;
    const requiredLevel = agentTypeLevels[requiredType] || 0;

    return userLevel >= requiredLevel;
  };

  /**
   * Check if user is a viewer (read-only)
   */
  const isViewer = (): boolean => {
    return permissions?.agentType === 'viewer';
  };

  /**
   * Check if user is a contributor or higher
   */
  const isContributor = (): boolean => {
    return hasAgentTypeLevel('contributor');
  };

  /**
   * Check if user is a content manager or higher
   */
  const isContentManager = (): boolean => {
    return hasAgentTypeLevel('content-manager');
  };

  /**
   * Check if user is a corpus manager (highest level)
   */
  const isCorpusManager = (): boolean => {
    return permissions?.agentType === 'corpus-manager';
  };

  return {
    permissions,
    loading,
    error,
    canUseTool,
    hasAgentTypeLevel,
    isViewer,
    isContributor,
    isContentManager,
    isCorpusManager,
    refetch: fetchPermissions
  };
}

/**
 * Hook to get agent type hierarchy information
 */
export function useAgentTypeHierarchy() {
  const [hierarchy, setHierarchy] = useState<AgentTypeInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHierarchy();
  }, []);

  const fetchHierarchy = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/admin/chatbot/agent-type-hierarchy`, {
        headers: getAuthHeadersOnly()
      });

      if (!response.ok) {
        throw new Error('Failed to fetch hierarchy');
      }

      const data = await response.json();
      setHierarchy(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load hierarchy');
      setHierarchy([]);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Get information about a specific agent type
   */
  const getAgentTypeInfo = (agentType: string): AgentTypeInfo | undefined => {
    return hierarchy.find(h => h.type === agentType);
  };

  return {
    hierarchy,
    loading,
    error,
    getAgentTypeInfo,
    refetch: fetchHierarchy
  };
}
