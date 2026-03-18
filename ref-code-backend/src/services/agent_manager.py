"""
Agent manager for session-based agent instances.
Handles agent creation, caching, and retrieval based on user permissions.
"""
from typing import Dict, Optional, Tuple
from google.adk.agents import Agent
import logging

from services.agent_loader import load_agent_config, create_agent_from_config, get_available_configs
from database.repositories.agent_repository import AgentRepository
from database.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

class AgentManager:
    """Manages agent instances for user sessions."""
    
    def __init__(self, project_id: str, location: str):
        """
        Initialize agent manager.
        
        Args:
            project_id: GCP project ID for Vertex AI
            location: Vertex AI location (e.g., 'us-west1')
        """
        self.project_id = project_id
        self.location = location
        self._agent_cache: Dict[str, Agent] = {}
        logger.info(f"AgentManager initialized with project={project_id}, location={location}")
    
    def get_agent_by_config_path(self, config_path: str) -> Agent:
        """
        Get or create agent instance by config path.
        Uses caching to avoid recreating agents.
        
        Args:
            config_path: Agent config path (e.g., 'develom', 'agent1')
            
        Returns:
            Agent instance
            
        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        # Check cache first
        if config_path in self._agent_cache:
            logger.debug(f"Returning cached agent for: {config_path}")
            return self._agent_cache[config_path]
        
        # Load and create agent
        logger.info(f"Loading new agent from config: {config_path}")
        config = load_agent_config(config_path)
        agent = create_agent_from_config(config, self.project_id, self.location)
        
        # Cache for future use
        self._agent_cache[config_path] = agent
        logger.info(f"Cached agent instance: {config_path}")
        
        return agent
    
    def get_agent_for_user(
        self, 
        user_id: int, 
        agent_id: Optional[int] = None
    ) -> Tuple[Agent, Dict]:
        """
        Get agent instance for a user.
        
        Args:
            user_id: User ID
            agent_id: Specific agent ID, or None for user's default
            
        Returns:
            Tuple of (Agent instance, agent metadata dict)
            
        Raises:
            ValueError: If user doesn't have access to agent or agent not found
        """
        # Determine which agent to load
        if agent_id is None:
            # Get user's default agent
            user = UserRepository.get_by_id(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            if not user.get('default_agent_id'):
                # If no default, try to get first accessible agent
                accessible_agents = AgentRepository.get_user_agents(user_id)
                if not accessible_agents:
                    raise ValueError(f"User {user_id} has no accessible agents")
                agent_id = accessible_agents[0]['id']
                logger.info(f"No default agent for user {user_id}, using first accessible: {agent_id}")
            else:
                agent_id = user['default_agent_id']
        
        # Verify user has access to this agent
        if not AgentRepository.has_access(user_id, agent_id):
            raise ValueError(
                f"User {user_id} does not have access to agent {agent_id}. "
                f"Check user_agent_access table."
            )
        
        # Get agent details from database
        agent_data = AgentRepository.get_by_id(agent_id)
        if not agent_data:
            raise ValueError(f"Agent {agent_id} not found in database")
        
        # Load agent by config_path
        config_path = agent_data['config_path']
        agent = self.get_agent_by_config_path(config_path)
        
        logger.info(
            f"Loaded agent for user {user_id}: "
            f"{agent_data['name']} (id={agent_id}, config={config_path})"
        )
        
        return agent, agent_data
    
    def get_agent_by_id(self, agent_id: int) -> Tuple[Agent, Dict]:
        """
        Get agent instance by agent ID (without user validation).
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Tuple of (Agent instance, agent metadata dict)
            
        Raises:
            ValueError: If agent not found
        """
        agent_data = AgentRepository.get_by_id(agent_id)
        if not agent_data:
            raise ValueError(f"Agent {agent_id} not found")
        
        config_path = agent_data['config_path']
        agent = self.get_agent_by_config_path(config_path)
        
        return agent, agent_data
    
    def validate_user_agent_access(self, user_id: int, agent_id: int) -> bool:
        """
        Validate if user has access to an agent.
        
        Args:
            user_id: User ID
            agent_id: Agent ID
            
        Returns:
            True if user has access, False otherwise
        """
        return AgentRepository.has_access(user_id, agent_id)
    
    def get_user_agents(self, user_id: int) -> list:
        """
        Get all agents accessible to a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of agent metadata dicts
        """
        return AgentRepository.get_user_agents(user_id)
    
    def clear_cache(self, config_path: Optional[str] = None):
        """
        Clear agent cache.
        
        Args:
            config_path: Specific config to clear, or None to clear all
        """
        if config_path:
            if config_path in self._agent_cache:
                del self._agent_cache[config_path]
                logger.info(f"Cleared cache for: {config_path}")
        else:
            self._agent_cache.clear()
            logger.info("Cleared entire agent cache")
    
    def reload_agent(self, config_path: str) -> Agent:
        """
        Force reload an agent from config (bypassing cache).
        
        Args:
            config_path: Agent config path
            
        Returns:
            Reloaded Agent instance
        """
        # Clear from cache
        if config_path in self._agent_cache:
            del self._agent_cache[config_path]
        
        # Reload
        return self.get_agent_by_config_path(config_path)
    
    def get_cache_info(self) -> Dict:
        """Get information about cached agents."""
        return {
            "cached_agents": list(self._agent_cache.keys()),
            "cache_size": len(self._agent_cache),
            "available_configs": get_available_configs()
        }
