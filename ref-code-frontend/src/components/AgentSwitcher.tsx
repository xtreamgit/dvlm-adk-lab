"use client";

import { useState } from 'react';
import { Agent } from '../lib/api-enhanced';

interface AgentSwitcherProps {
  currentAgent: Agent | null;
  availableAgents: Agent[];
  isLoading?: boolean;
}

export default function AgentSwitcher({ currentAgent, availableAgents, isLoading }: AgentSwitcherProps) {
  const [showDetails, setShowDetails] = useState(false);

  if (isLoading) {
    return (
      <div className="px-3 py-2 rounded-lg border border-gray-200 bg-gray-50">
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2" style={{ borderColor: 'rgb(0,84,64)' }}></div>
          <span className="text-sm text-gray-600">Loading agent...</span>
        </div>
      </div>
    );
  }

  if (!currentAgent) {
    return (
      <div className="px-3 py-2 rounded-lg border border-yellow-200 bg-yellow-50">
        <div className="flex items-center space-x-2">
          <svg className="w-4 h-4 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span className="text-sm text-yellow-800">No agent assigned</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {/* Current Agent Display */}
      <div 
        className="px-3 py-2 rounded-lg border cursor-pointer transition-all"
        style={{ 
          borderColor: 'rgb(0,84,64)', 
          backgroundColor: 'rgb(240, 253, 244)' 
        }}
        onClick={() => setShowDetails(!showDetails)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <svg className="w-4 h-4" style={{ color: 'rgb(0,84,64)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <div>
              <div className="text-sm font-medium" style={{ color: 'rgb(0,84,64)' }}>
                {currentAgent.display_name}
              </div>
              <div className="text-xs text-gray-600">
                {currentAgent.agent_type}
              </div>
            </div>
          </div>
          <svg 
            className={`w-4 h-4 text-gray-400 transition-transform ${showDetails ? 'rotate-180' : ''}`} 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {/* Agent Details (Expandable) */}
      {showDetails && (
        <div className="px-3 py-2 rounded-lg border border-gray-200 bg-white text-xs space-y-2">
          {currentAgent.description && (
            <div>
              <div className="font-medium text-gray-700 mb-1">Description:</div>
              <div className="text-gray-600">{currentAgent.description}</div>
            </div>
          )}
          
          <div>
            <div className="font-medium text-gray-700 mb-1">Available Tools ({currentAgent.tools.length}):</div>
            <div className="flex flex-wrap gap-1">
              {currentAgent.tools.map((tool, idx) => (
                <span 
                  key={idx} 
                  className="px-2 py-0.5 rounded text-xs"
                  style={{ backgroundColor: 'rgb(220, 252, 231)', color: 'rgb(0,84,64)' }}
                >
                  {tool}
                </span>
              ))}
            </div>
          </div>

          {availableAgents.length > 1 && (
            <div className="pt-2 border-t border-gray-200">
              <div className="text-gray-500 italic">
                Note: You have access to {availableAgents.length} agents. Contact your administrator to change your assigned agent.
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
