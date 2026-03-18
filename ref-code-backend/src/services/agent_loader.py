"""
Dynamic agent configuration loader.
Loads agent configs from JSON files and creates Agent instances.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any
from google.adk.agents import Agent
from google.adk.models import Gemini
import logging

from services.tool_registry import get_tools_by_names

logger = logging.getLogger(__name__)

# Base directory for agent configurations
AGENT_CONFIG_DIR = Path(__file__).parent.parent.parent / "config" / "agent_instructions"

def load_agent_config(config_path: str) -> Dict[str, Any]:
    """
    Load agent configuration from JSON file.
    
    Args:
        config_path: Path identifier for agent (e.g., 'develom', 'agent1')
        
    Returns:
        Dictionary with agent configuration
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
    """
    config_file = AGENT_CONFIG_DIR / f"{config_path}.json"
    
    if not config_file.exists():
        raise FileNotFoundError(
            f"Agent config not found: {config_file}\n"
            f"Looking for: {config_path}.json in {AGENT_CONFIG_DIR}"
        )
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        logger.info(f"Loaded agent config: {config.get('agent_name')} from {config_path}.json")
        return config
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file {config_file}: {e}")
        raise

def build_instruction_from_config(config: Dict[str, Any]) -> str:
    """
    Build instruction string from JSON config structure.
    
    Args:
        config: Agent configuration dictionary
        
    Returns:
        Formatted instruction string for agent
    """
    instruction_data = config.get('instruction', {})
    instruction_parts = []
    
    # Title
    if 'title' in instruction_data:
        instruction_parts.append(f"# {instruction_data['title']}\n\n")
    
    # Role
    if 'role' in instruction_data:
        instruction_parts.append(instruction_data['role'] + "\n\n")
    
    # Capabilities
    if 'capabilities' in instruction_data:
        instruction_parts.append("## Your Capabilities\n\n")
        for i, cap in enumerate(instruction_data['capabilities'], 1):
            instruction_parts.append(f"{i}. **{cap}**\n")
        instruction_parts.append("\n")
    
    # Approach
    if 'approach' in instruction_data:
        instruction_parts.append("## How to Approach User Requests\n\n")
        instruction_parts.append("When a user asks a question:\n")
        for i, step in enumerate(instruction_data['approach'], 1):
            instruction_parts.append(f"{i}. {step}\n")
        instruction_parts.append("\n")
    
    # Tool descriptions
    if 'tool_descriptions' in instruction_data:
        instruction_parts.append("## Using Tools\n\n")
        instruction_parts.append(f"You have {len(instruction_data['tool_descriptions'])} specialized tools at your disposal:\n\n")
        
        for i, (tool_name, tool_info) in enumerate(instruction_data['tool_descriptions'].items(), 1):
            instruction_parts.append(f"{i}. `{tool_name}`: {tool_info['description']}\n")
            
            if tool_info.get('parameters'):
                instruction_parts.append("   - Parameters:\n")
                for param, desc in tool_info['parameters'].items():
                    instruction_parts.append(f"     - {param}: {desc}\n")
            
            if tool_info.get('note'):
                instruction_parts.append(f"   - Note: {tool_info['note']}\n")
            
            if tool_info.get('warning'):
                instruction_parts.append(f"   - ⚠️ Warning: {tool_info['warning']}\n")
            
            instruction_parts.append("\n")
    
    # Internal details
    if 'internal_details' in instruction_data:
        instruction_parts.append("## INTERNAL: Technical Implementation Details\n\n")
        instruction_parts.append("This section is NOT user-facing information - don't repeat these details to users:\n\n")
        for detail in instruction_data['internal_details']:
            instruction_parts.append(f"- {detail}\n")
        instruction_parts.append("\n")
    
    # Communication guidelines
    if 'communication_guidelines' in instruction_data:
        instruction_parts.append("## Communication Guidelines\n\n")
        for guideline in instruction_data['communication_guidelines']:
            instruction_parts.append(f"- {guideline}\n")
        instruction_parts.append("\n")
    
    instruction_parts.append("Remember, your primary goal is to help users access and manage information through RAG capabilities.\n")
    
    return "".join(instruction_parts)

def create_agent_from_config(
    config: Dict[str, Any],
    project_id: str,
    location: str
) -> Agent:
    """
    Create Agent instance from configuration.
    
    Args:
        config: Agent configuration dictionary
        project_id: GCP project ID
        location: Vertex AI location
        
    Returns:
        Configured Agent instance
        
    Raises:
        ValueError: If required config fields are missing
    """
    # Validate required fields
    required_fields = ['agent_name', 'tools', 'instruction']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field in agent config: {field}")
    
    # Get model configuration
    model_config = config.get('model', {})
    model_type = model_config.get('type', 'gemini-2.5-flash')
    model_location = model_config.get('location', location)
    
    # Set environment variables for Vertex AI
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
    os.environ["VERTEXAI_PROJECT"] = project_id
    os.environ["VERTEXAI_LOCATION"] = model_location
    
    # Create Vertex AI model
    vertex_model = Gemini(model=model_type, location=model_location)
    
    # Get tools for this agent
    tool_names = config.get('tools', [])
    if not tool_names:
        logger.warning(f"Agent '{config['agent_name']}' has no tools configured")
    
    tools = get_tools_by_names(tool_names)
    
    # Build instruction string
    instruction = build_instruction_from_config(config)
    
    # Create Agent instance
    agent = Agent(
        name=config['agent_name'],
        model=vertex_model,
        description=config.get('description', ''),
        tools=tools,
        instruction=instruction
    )
    
    logger.info(
        f"Created agent '{config['agent_name']}' "
        f"(display: {config.get('display_name', 'N/A')}) "
        f"with {len(tools)} tools: {tool_names}"
    )
    
    return agent

def get_available_configs() -> list:
    """Get list of available agent configuration files."""
    if not AGENT_CONFIG_DIR.exists():
        return []
    
    configs = [
        f.stem for f in AGENT_CONFIG_DIR.glob("*.json")
    ]
    return sorted(configs)
