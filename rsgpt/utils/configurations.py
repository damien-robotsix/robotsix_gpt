from pydantic import BaseModel, Field


class LlmConfig(BaseModel):
    model: str = Field(description="Llm model to use.")


class RsgptConfig(BaseModel):
    llm_config: LlmConfig
