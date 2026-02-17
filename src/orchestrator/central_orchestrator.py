"""Central orchestrator for coordinating all agents."""

from typing import Dict, Any, Optional, List
import logging
from collections import defaultdict

from src.orchestrator.base_agent import BaseAgent
from src.utils.logging import setup_logging

logger = setup_logging()


class CentralOrchestrator:
    """Coordinates specialized sub-agents."""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_queue: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.logger = logger
    
    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the orchestrator."""
        agent_name = agent.name
        if agent_name in self.agents:
            self.logger.warning(f"Agent {agent_name} already registered, overwriting")
        
        self.agents[agent_name] = agent
        agent.orchestrator = self
        self.logger.info(f"Registered agent: {agent_name}")
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Get a registered agent by name."""
        return self.agents.get(agent_name)
    
    def route_message(
        self,
        target_agent: str,
        message: Dict[str, Any],
        sender: Optional[str] = None
    ) -> None:
        """Route a message to a target agent."""
        if target_agent not in self.agents:
            self.logger.error(f"Agent {target_agent} not found")
            return
        
        self.message_queue[target_agent].append({
            "sender": sender,
            "message": message,
            "timestamp": self._get_timestamp()
        })
        
        self.logger.info(f"Routed message from {sender} to {target_agent}")
    
    def get_messages(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get queued messages for an agent."""
        messages = self.message_queue.get(agent_name, [])
        # Clear queue after reading
        self.message_queue[agent_name] = []
        return messages
    
    async def execute_workflow(
        self,
        workflow: List[Dict[str, Any]],
        initial_input: Any
    ) -> Dict[str, Any]:
        """
        Execute a workflow of agent tasks.
        
        Args:
            workflow: List of task definitions, e.g.:
                [
                    {"agent": "VoiceCaptureAgent", "input": initial_input},
                    {"agent": "ProfileParserAgent", "input": "{{previous.output}}"}
                ]
            initial_input: Initial input data
        
        Returns:
            Final workflow result
        """
        self.logger.info(f"Executing workflow with {len(workflow)} steps")
        
        context = {"initial_input": initial_input}
        
        for i, step in enumerate(workflow):
            agent_name = step["agent"]
            agent = self.get_agent(agent_name)
            
            if not agent:
                raise ValueError(f"Agent {agent_name} not found")
            
            # Resolve input (support template variables)
            step_input = step.get("input", initial_input)
            if isinstance(step_input, str) and "{{" in step_input:
                # Simple template resolution
                step_input = step_input.replace("{{previous.output}}", str(context.get("previous_output", "")))
            
            self.logger.info(f"Step {i+1}: Executing {agent_name}")
            
            # Execute agent
            result = await agent.execute(step_input, **step.get("kwargs", {}))
            
            if not result["success"]:
                self.logger.error(f"Step {i+1} failed: {result.get('error')}")
                return {
                    "success": False,
                    "error": result.get("error"),
                    "failed_step": i+1,
                    "context": context
                }
            
            # Store result in context
            context[f"step_{i+1}_output"] = result["output"]
            context["previous_output"] = result["output"]
        
        return {
            "success": True,
            "final_output": context["previous_output"],
            "context": context
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def list_agents(self) -> List[str]:
        """List all registered agents."""
        return list(self.agents.keys())
