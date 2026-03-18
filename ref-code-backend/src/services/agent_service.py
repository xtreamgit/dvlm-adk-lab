"""
Agent service for managing agents and user access.
"""

import logging
from typing import Optional, List

from database.repositories.agent_repository import AgentRepository
from database.repositories.user_repository import UserRepository
from models.agent import Agent, AgentCreate, AgentWithAccess

logger = logging.getLogger(__name__)


class AgentService:
    """Service for agent operations."""
    
    @staticmethod
    def create_agent(agent_create: AgentCreate) -> Agent:
        """
        Create a new agent.
        
        Args:
            agent_create: AgentCreate model with agent data
            
        Returns:
            Created Agent object
            
        Raises:
            ValueError: If agent name already exists
        """
        # Check if agent name exists
        if AgentRepository.get_by_name(agent_create.name):
            raise ValueError(f"Agent '{agent_create.name}' already exists")
        
        # Check if config_path exists
        if AgentRepository.get_by_config_path(agent_create.config_path):
            raise ValueError(f"Agent with config_path '{agent_create.config_path}' already exists")
        
        agent_dict = AgentRepository.create(
            name=agent_create.name,
            display_name=agent_create.display_name,
            config_path=agent_create.config_path,
            description=agent_create.description
        )
        
        logger.info(f"Agent created: {agent_create.name} (ID: {agent_dict['id']})")
        return Agent(**agent_dict)
    
    @staticmethod
    def get_agent_by_id(agent_id: int) -> Optional[Agent]:
        """Get agent by ID."""
        agent_dict = AgentRepository.get_by_id(agent_id)
        return Agent(**agent_dict) if agent_dict else None
    
    @staticmethod
    def get_agent_by_name(name: str) -> Optional[Agent]:
        """Get agent by name."""
        agent_dict = AgentRepository.get_by_name(name)
        return Agent(**agent_dict) if agent_dict else None
    
    @staticmethod
    def get_all_agents(active_only: bool = True) -> List[Agent]:
        """Get all agents."""
        agents_dict = AgentRepository.get_all(active_only=active_only)
        return [Agent(**a) for a in agents_dict]
    
    @staticmethod
    def update_agent(agent_id: int, **kwargs) -> Optional[Agent]:
        """
        Update agent fields.
        
        Args:
            agent_id: Agent ID
            **kwargs: Fields to update
            
        Returns:
            Updated Agent object or None if not found
        """
        agent_dict = AgentRepository.update(agent_id, **kwargs)
        return Agent(**agent_dict) if agent_dict else None
    
    # ========== User-Agent Access ==========
    
    @staticmethod
    def grant_user_access(user_id: int, agent_id: int) -> bool:
        """
        Grant user access to an agent.
        
        Args:
            user_id: User ID
            agent_id: Agent ID
            
        Returns:
            True if successful, False otherwise
        """
        success = AgentRepository.grant_access(user_id, agent_id)
        if success:
            logger.info(f"User {user_id} granted access to agent {agent_id}")
        return success
    
    @staticmethod
    def revoke_user_access(user_id: int, agent_id: int) -> bool:
        """
        Revoke user access to an agent.
        
        Args:
            user_id: User ID
            agent_id: Agent ID
            
        Returns:
            True if successful, False otherwise
        """
        success = AgentRepository.revoke_access(user_id, agent_id)
        if success:
            logger.info(f"User {user_id} access revoked for agent {agent_id}")
        return success
    
    @staticmethod
    def validate_agent_access(user_id: int, agent_id: int) -> bool:
        """
        Check if user has access to an agent.
        
        Args:
            user_id: User ID
            agent_id: Agent ID
            
        Returns:
            True if user has access, False otherwise
        """
        return AgentRepository.has_access(user_id, agent_id)
    
    @staticmethod
    def get_user_agents(user_id: int, active_only: bool = True) -> List[AgentWithAccess]:
        """
        Get all agents a user has access to.
        
        Args:
            user_id: User ID
            active_only: Only return active agents
            
        Returns:
            List of AgentWithAccess objects
        """
        agents_dict = AgentRepository.get_user_agents(user_id, active_only=active_only)
        
        # Get user's default agent
        user_dict = UserRepository.get_by_id(user_id)
        default_agent_id = user_dict.get('default_agent_id') if user_dict else None
        
        # Load tools from agent config files
        from services.agent_loader import load_agent_config
        
        agents = []
        for agent_data in agents_dict:
            agent_type = None
            tools = []
            config_path = agent_data.get('config_path')
            if config_path:
                try:
                    config = load_agent_config(config_path)
                    tools = config.get('tools', [])
                    agent_type = config.get('agent_name', config_path)
                except Exception:
                    logger.warning(f"Could not load config for agent {config_path}")
            
            agent = AgentWithAccess(
                **agent_data,
                has_access=True,
                is_default=(agent_data['id'] == default_agent_id),
                agent_type=agent_type,
                tools=tools
            )
            agents.append(agent)
        
        return agents
    
    @staticmethod
    def get_default_agent(user_id: int) -> Optional[Agent]:
        """
        Get user's default agent.
        
        Args:
            user_id: User ID
            
        Returns:
            Agent object or None if no default set
        """
        user_dict = UserRepository.get_by_id(user_id)
        if not user_dict or not user_dict.get('default_agent_id'):
            return None
        
        agent_dict = AgentRepository.get_by_id(user_dict['default_agent_id'])
        return Agent(**agent_dict) if agent_dict else None
    
    @staticmethod
    def set_default_agent(user_id: int, agent_id: int) -> bool:
        """
        Set user's default agent.
        
        Args:
            user_id: User ID
            agent_id: Agent ID
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ValueError: If user doesn't have access to the agent
        """
        # Validate user has access to the agent
        if not AgentRepository.has_access(user_id, agent_id):
            raise ValueError(f"User {user_id} does not have access to agent {agent_id}")
        
        # Update user's default agent
        user_dict = UserRepository.update(user_id, default_agent_id=agent_id)
        success = user_dict is not None
        
        if success:
            logger.info(f"User {user_id} default agent set to {agent_id}")
        
        return success
