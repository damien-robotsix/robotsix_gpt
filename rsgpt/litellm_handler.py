from pydantic import BaseModel
from litellm import completion, Choices
from litellm.files.main import ModelResponse


class LlmConfig(BaseModel):
    model: str


class LLMHandler:
    _config: LlmConfig

    def __init__(self, config: LlmConfig):
        self._config = config

    def get_answer(
        self, prompt: str, response_format: type[BaseModel] | None
    ) -> str | None:
        print("User prompt: ", prompt)
        messages = [{"role": "user", "content": prompt}]
        response = completion(
            model=self._config.model, messages=messages, response_format=response_format
        )
        assert isinstance(response, ModelResponse)
        choice = response.choices[0]
        assert isinstance(choice, Choices)
        return choice.message.content
