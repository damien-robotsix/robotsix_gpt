from ..litellm_handler import LLMHandler
from pydantic import BaseModel


class Agent:
    def __init__(self, llm_handler: LLMHandler, args: BaseModel | None = None):
        self._llm_handler: LLMHandler = llm_handler
        self._system_prompt: str = ""
        self._output_schema: str = ""

    @classmethod
    def agent_arguments(cls) -> type[BaseModel] | None:
        return None

    @classmethod
    def agent_description(cls) -> str:
        return ""

    def trigger(self) -> list[dict[str, str]] | None:
        return None
