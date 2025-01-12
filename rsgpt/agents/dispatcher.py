from typing import override
from ..litellm_handler import LLMHandler
from .agent import Agent
from .file_creator import FileCreator
from pydantic import BaseModel, Field
import json


class DispatcherOutput(BaseModel):
    agent_name: str = Field(description="The name of the agent to be dispatched")
    agent_args: str = Field(
        description="The arguments to be passed to the agent as a JSON schema"
    )
    agent_prompt: str = Field(description="The prompt to be sent to the agent")


class Dispatcher(Agent):
    def __init__(self, llm_handler: LLMHandler, args: None = None):
        super().__init__(llm_handler, args)
        self._agents: dict[str, type[Agent]] = {"FileCreator": FileCreator}
        self._system_prompt: str = (
            "You are a dispatcher agent. You can dispatch tasks to different agents."
            + "The available agents are: \n"
        )
        for agent in self._agents:
            self._system_prompt += agent + " with arguments \n"
            arguments = self._agents[agent].agent_arguments()
            if arguments:
                self._system_prompt += json.dumps(arguments.model_json_schema()) + "\n"
        self._system_prompt += "\n"

    @override
    def trigger(self, prompt: str) -> str:
        # Use LLM to predict the correct agent and arguments
        response = self._llm_handler.get_answer(
            self._system_prompt + prompt, DispatcherOutput
        )
        assert response is not None
        response_pydentic = DispatcherOutput.model_validate_json(response)
        agent_name = response_pydentic.agent_name
        agent_args = response_pydentic.agent_args
        agent_args_pydantic = self._agents[agent_name].agent_arguments()
        print(agent_args)
        if agent_args_pydantic:
            agent_args_pydantic_instance = agent_args_pydantic.model_validate_json(
                agent_args
            )
        else:
            return "An error occurred while validating the agent arguments"
        agent_prompt = response_pydentic.agent_prompt
        dispatched_agent = self._agents[agent_name](
            self._llm_handler, agent_args_pydantic_instance
        )
        return dispatched_agent.trigger(agent_prompt)

