"""Factory for creating and configuring agents."""

from typing import List, Any, Dict

from smolagents import CodeAgent, ToolCallingAgent, DuckDuckGoSearchTool
from smolagents.cli import load_model

from utils.config import load_config, save_config


class AgentFactory:
    """Factory class for creating and configuring different types of agents."""

    def __init__(self, config: Dict[str, Any], experiment_config: Dict[str, Any]):
        self.config = config
        self.experiment_config = experiment_config

    def create_meta_agents(self) -> List[Any]:
        """Create meta agents based on experiment configuration.

        Returns:
            List of configured meta agents
        """
        # Load and update meta agent configuration
        meta_agent_config = load_config(self.config['meta_agent'])
        meta_agent_config['model-id'] = self.experiment_config['model-id']
        save_config(self.config['meta_agent'], meta_agent_config)

        # Create tools
        tools = self._create_tools()
        tools_2 = self._create_secondary_tools()
        managed_agents = self._create_managed_agents()

        # Create model
        model = load_model(
            meta_agent_config['model-type'],
            meta_agent_config['model-id'],
            meta_agent_config['model-api'],
            meta_agent_config['api-key'],
            meta_agent_config['api-base']
        )

        # Create agents based on experiment type
        meta_agent, meta_agent2 = self._create_agent_pair(
            tools, tools_2, managed_agents, meta_agent_config, model
        )

        # Set max steps if specified
        if hasattr(self.experiment_config, 'step'):
            meta_agent.max_steps = int(self.experiment_config.get('step', 3))

        return [meta_agent, meta_agent2]

    def _create_tools(self) -> List[Any]:
        """Create primary tools based on experiment configuration."""
        tools = []

        if self.experiment_config['agent'] is None:
            return tools

        # Import agents as needed
        if 'web' in self.experiment_config['agent']:
            tools.append(DuckDuckGoSearchTool())

        if 'qav' in self.experiment_config['agent']:
            from ..agents.qastorage_agent import QAVectorSearchCalling
            tools.append(QAVectorSearchCalling())

        if 'desv' in self.experiment_config['agent']:
            from ..agents.qastorage_agent import PVectorSearchCalling
            tools.append(PVectorSearchCalling())

        if 'attv' in self.experiment_config['agent']:
            from ..agents.qastorage_agent import AVectorSearchCalling
            tools.append(AVectorSearchCalling())

        if 'product' in self.experiment_config['agent']:
            from ..agents.product_agent import RVSQLAgentCalling
            tools.append(RVSQLAgentCalling())

        if 'webtv' in self.experiment_config['agent']:
            from ..agents.web_tavily_agent import TavilySearch
            tools.append(TavilySearch())

        return tools

    def _create_secondary_tools(self) -> List[Any]:
        """Create secondary tools for second agent."""
        tools_2 = []

        if self.experiment_config['agent'] is None:
            return tools_2

        if 'qav' in self.experiment_config['agent']:
            from ..agents.qastorage_agent import QAVectorSearchCalling
            tools_2.append(QAVectorSearchCalling())

        if 'desv' in self.experiment_config['agent']:
            from ..agents.qastorage_agent import PVectorSearchCalling
            tools_2.append(PVectorSearchCalling())

        if 'attv' in self.experiment_config['agent']:
            from ..agents.qastorage_agent import AVectorSearchCalling
            tools_2.append(AVectorSearchCalling())

        return tools_2

    def _create_managed_agents(self) -> List[Any]:
        """Create managed agents (like web agents)."""
        managed_agents = []

        if (self.experiment_config['agent'] is not None and
            'web' in self.experiment_config['agent']):
            # Note: Web agent creation would go here if needed
            pass

        return managed_agents

    def _create_agent_pair(self, tools: List[Any], tools_2: List[Any],
                          managed_agents: List[Any], meta_agent_config: Dict[str, Any],
                          model: Any) -> tuple:
        """Create pair of meta agents based on experiment configuration."""
        model_loader = lambda: load_model(
            meta_agent_config['model-type'],
            meta_agent_config['model-id'],
            meta_agent_config['model-api'],
            meta_agent_config['api-key'],
            meta_agent_config['api-base']
        )

        if 'plan' in self.experiment_config['agent']:
            meta_agent = ToolCallingAgent(
                tools=tools,
                model=model_loader(),
                managed_agents=managed_agents,
                planning_interval=1,
            )
            meta_agent2 = ToolCallingAgent(
                tools=tools_2,
                model=model_loader(),
            )

        elif 'plancode' in self.experiment_config['agent']:
            meta_agent = CodeAgent(
                tools=tools,
                model=model_loader(),
                managed_agents=managed_agents,
                additional_authorized_imports=['time', 'numpy', 'pandas'],
                planning_interval=1
            )
            meta_agent2 = CodeAgent(
                tools=tools_2,
                model=model_loader(),
                additional_authorized_imports=['time', 'numpy', 'pandas'],
            )

        else:
            meta_agent = CodeAgent(
                tools=tools,
                model=model_loader(),
                managed_agents=managed_agents,
                additional_authorized_imports=['time', 'numpy', 'pandas'],
            )
            meta_agent2 = CodeAgent(
                tools=tools_2,
                model=model_loader(),
                additional_authorized_imports=['time', 'numpy', 'pandas'],
            )

        return meta_agent, meta_agent2

    def create_base_model(self) -> Any:
        """Create base model for text-only evaluation."""
        meta_agent_config = load_config(self.config['meta_agent'])
        return load_model(
            meta_agent_config['model-type'],
            meta_agent_config['model-id'],
            meta_agent_config['model-api'],
            meta_agent_config['api-key'],
            meta_agent_config['api-base']
        )