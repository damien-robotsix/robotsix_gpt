from .configurations import LlmConfig
from pydantic import BaseModel
from litellm import completion, Choices
from litellm.files.main import ModelResponse
import json


class LLMHandler:
    _config: LlmConfig

    def __init__(self, config: LlmConfig):
        self._config = config

    def get_answer(
        self, messages: list[dict[str, str]], response_format: type[BaseModel] | None
    ) -> str | None:
        print(messages)
        print("\n \n")
        response = completion(
            model=self._config.model, messages=messages, response_format=response_format
        )
        assert isinstance(response, ModelResponse)
        choice = response.choices[0]
        assert isinstance(choice, Choices)
        output = choice.message
        output = json.loads(output.model_dump_json())
        return output["content"]
