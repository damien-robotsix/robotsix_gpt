import json

from typing import override

from rsgpt.utils.litellm_handler import LLMHandler
from .agent import Agent
from pydantic import BaseModel, Field
from .agent_registry import all_agents


class DispatcherArgs(BaseModel):
    messages: list[dict[str, str]] = Field(
        description="The prompt to be sent to the agent"
    )


class DispatcherOutput(BaseModel):
    agent_name: str = Field(description="The name of the agent to be dispatched")
    agent_args: str = Field(
        description="The arguments to be passed to the agent as a JSON schema"
    )


class Dispatcher(Agent):
    def __init__(self, llm_handler: LLMHandler, args: DispatcherArgs):
        super().__init__(llm_handler)
        self._agents: dict[str, type[Agent]] = all_agents
        self._system_prompt: str = (
            "You are a dispatcher agent. You can dispatch tasks to different agents."
            + "The available agents are: \n"
        )
        for agent in self._agents:
            self._system_prompt += (
                agent
                + ", Agent description: \n"
                + self._agents[agent].agent_description()
                + ", Agent arguments: \n"
            )
            arguments = self._agents[agent].agent_arguments()
            if arguments:
                self._system_prompt += json.dumps(arguments.model_json_schema()) + "\n"
        self._system_prompt += "\n"
        self._messages: list[dict[str, str]] = args.messages

    @override
    def trigger(self) -> list[dict[str, str]] | None:
        input_messages = [
            {"role": "system", "content": self._system_prompt},
        ]
        for message in self._messages:
            if message["role"]:
                if message["role"] != "system":
                    input_messages.append(message)
        response = self._llm_handler.get_answer(input_messages, DispatcherOutput)
        assert response is not None
        response_pydentic = DispatcherOutput.model_validate_json(response)
        agent_name = response_pydentic.agent_name
        agent_args = response_pydentic.agent_args
        agent_args_pydantic = self._agents[agent_name].agent_arguments()
        agent_args_pydantic_instance = None
        if agent_args_pydantic:
            agent_args_pydantic_instance = agent_args_pydantic.model_validate_json(
                agent_args
            )
        print("Agent name:", agent_name, ", Agent args:", agent_args, ",\n")
        dispatched_agent = self._agents[agent_name](
            self._llm_handler, agent_args_pydantic_instance
        )
        agent_output = dispatched_agent.trigger()
        if agent_output:
            input_messages += [{"role": "assistant", "content": response}]
            input_messages += agent_output
            dispacther_args = DispatcherArgs(messages=input_messages)
            inner_dispacther = Dispatcher(self._llm_handler, dispacther_args)
            return inner_dispacther.trigger()
