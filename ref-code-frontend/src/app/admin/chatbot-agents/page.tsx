'use client';

import { useState, useEffect } from 'react';
import { getAuthHeadersOnly } from '../../../lib/auth-headers';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || '';

interface ChatbotAgent {
  id: number;
  name: string;
  display_name: string;
  description: string | null;
  agent_type: string;
  tools: string[];
  is_active: boolean;
  created_at: string;
}

interface ChatbotGroup {
  id: number;
  name: string;
  description?: string;
}

interface GroupAgent {
  id: number;
  name: string;
  display_name: string;
  agent_type: string;
  tools: string[];
  can_use: boolean;
  granted_at: string;
}

export default function ChatbotAgentsPage() {
  const [agents, setAgents] = useState<ChatbotAgent[]>([]);
  const [groups, setGroups] = useState<ChatbotGroup[]>([]);
  const [groupAgents, setGroupAgents] = useState<Map<number, GroupAgent[]>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showGrantDialog, setShowGrantDialog] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<ChatbotAgent | null>(null);
  const [selectedGroupId, setSelectedGroupId] = useState<number>(0);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const headers = getAuthHeadersOnly();

      // Fetch agents and groups
      const [agentsData, groupsData] = await Promise.all([
        fetch(`${BACKEND_URL}/api/admin/chatbot/agents`, { headers, credentials: 'include' }).then(r => r.json()),
        fetch(`${BACKEND_URL}/api/admin/chatbot/groups`, { headers, credentials: 'include' }).then(r => r.json()),
      ]);

      setAgents(agentsData);
      setGroups(groupsData);

      // Fetch agents for each group
      const groupAgentsMap = new Map<number, GroupAgent[]>();
      await Promise.all(
        groupsData.map(async (group: ChatbotGroup) => {
          const groupAgentsData = await fetch(
            `${BACKEND_URL}/api/admin/chatbot/groups/${group.id}/agents`,
            { headers, credentials: 'include' }
          ).then(r => r.json());
          groupAgentsMap.set(group.id, groupAgentsData);
        })
      );
      setGroupAgents(groupAgentsMap);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleAssignAgent = async () => {
    if (!selectedAgent || !selectedGroupId) {
      alert('Please select a group');
      return;
    }

    try {
      await fetch(`${BACKEND_URL}/api/admin/chatbot/groups/${selectedGroupId}/agents/${selectedAgent.id}`, {
        method: 'POST',
        headers: getAuthHeadersOnly(),
        credentials: 'include',
      });

      setShowGrantDialog(false);
      setSelectedGroupId(0);
      await loadData();
    } catch (err) {
      alert('Failed to assign agent to group');
    }
  };

  const handleRemoveAgent = async (groupId: number, agentId: number) => {
    if (!confirm('Remove this agent from the group?')) return;

    try {
      await fetch(`${BACKEND_URL}/api/admin/chatbot/groups/${groupId}/agents/${agentId}`, {
        method: 'DELETE',
        headers: getAuthHeadersOnly(),
        credentials: 'include',
      });
      await loadData();
    } catch (err) {
      alert('Failed to remove agent from group');
    }
  };

  const openGrantDialog = (agent: ChatbotAgent) => {
    setSelectedAgent(agent);
    setSelectedGroupId(0);
    setShowGrantDialog(true);
  };

  const getGroupsForAgent = (agentId: number): Array<{ group: ChatbotGroup; canUse: boolean }> => {
    const result: Array<{ group: ChatbotGroup; canUse: boolean }> = [];
    groups.forEach((group) => {
      const agents = groupAgents.get(group.id) || [];
      const agentAccess = agents.find(a => a.id === agentId);
      if (agentAccess) {
        result.push({ group, canUse: agentAccess.can_use });
      }
    });
    return result;
  };

  if (loading) return <div className="flex items-center justify-center min-h-screen"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  if (error) return <div className="flex items-center justify-center min-h-screen text-red-600">{error}</div>;

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Chatbot Agents</h1>
        <p className="text-gray-600">Manage agent types and their group assignments</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {agents.length === 0 ? (
          <div className="col-span-full bg-white rounded-lg shadow p-8 text-center text-gray-500">No agents available.</div>
        ) : agents.map((agent) => {
          const groupAssignments = getGroupsForAgent(agent.id);
          return (
            <div key={agent.id} className="bg-gray-100 rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 border-b bg-emerald-500">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h3 className="text-lg font-semibold text-white">🤖 {agent.display_name}</h3>
                    <p className="text-sm text-emerald-100">{agent.name}</p>
                  </div>
                  <button 
                    onClick={() => openGrantDialog(agent)} 
                    className="px-3 py-1 text-sm font-medium rounded bg-emerald-600 hover:bg-emerald-700 text-white"
                  >
                    + Assign
                  </button>
                </div>
                <div className="mt-2">
                  <span className="inline-block px-2 py-1 text-xs font-medium rounded bg-emerald-600 text-white">
                    {agent.agent_type}
                  </span>
                </div>
              </div>
              
              <div className="p-4">
                <div className="mb-3">
                  <div className="text-xs text-gray-500 uppercase font-medium mb-2">Tools ({agent.tools.length})</div>
                  <div className="flex flex-wrap gap-1">
                    {agent.tools.map((tool, idx) => (
                      <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="mt-4">
                  <div className="text-xs text-gray-500 uppercase font-medium mb-2">Group Assignments ({groupAssignments.length})</div>
                  {groupAssignments.length === 0 ? (
                    <p className="text-gray-400 italic text-sm">No groups assigned</p>
                  ) : (
                    <div className="space-y-2">
                      {groupAssignments.map(({ group, canUse }) => (
                        <div key={group.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                          <div>
                            <span className="font-medium text-sm">{group.name}</span>
                            {canUse && <span className="ml-2 px-2 py-0.5 rounded text-xs bg-green-100 text-green-800">Active</span>}
                          </div>
                          <button 
                            onClick={() => handleRemoveAgent(group.id, agent.id)} 
                            className="text-rose-600 hover:text-rose-800 text-xs font-medium"
                          >
                            Remove
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {showGrantDialog && selectedAgent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Assign Agent to Group</h2>
            <div className="mb-4 p-3 bg-gray-50 rounded">
              <div className="font-semibold text-gray-900">{selectedAgent.display_name}</div>
              <div className="text-sm text-gray-500 mt-1">Type: {selectedAgent.agent_type}</div>
              <div className="text-xs text-gray-500 mt-2">
                Tools: {selectedAgent.tools.join(', ')}
              </div>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Select Group *</label>
                <select 
                  value={selectedGroupId} 
                  onChange={(e) => setSelectedGroupId(parseInt(e.target.value))} 
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  <option value={0}>Choose a group...</option>
                  {groups.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.name}
                      {g.description ? ` - ${g.description}` : ''}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            
            <div className="flex justify-end gap-2 mt-6">
              <button 
                onClick={() => setShowGrantDialog(false)} 
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded"
              >
                Cancel
              </button>
              <button 
                onClick={handleAssignAgent} 
                className="px-4 py-2 text-white rounded hover:opacity-90"
                style={{ backgroundColor: 'rgb(0,84,64)' }}
              >
                Assign Agent
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
