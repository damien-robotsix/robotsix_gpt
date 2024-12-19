from langchain_openai import ChatOpenAI
from os import getenv
from langchain.callbacks.base import BaseCallbackHandler


class InputDisplayCallbackHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        print("\n--- INPUT SENT TO LLM ---")
        for prompt in prompts:
            print(prompt)
        print("-------------------------\n")


class OutputDisplayCallbackHandler(BaseCallbackHandler):
    def on_llm_end(self, response, **kwargs):
        print("\n--- OUTPUT FROM LLM ---")
        print(response)
        print("-------------------------\n")


input_display_callback = InputDisplayCallbackHandler()
output_display_callback = OutputDisplayCallbackHandler()

llm_base = ChatOpenAI(
    openai_api_key=getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    model_name="openai/gpt-4o-2024-11-20",
    callbacks=[input_display_callback, output_display_callback],
)

llm_think = ChatOpenAI(
    openai_api_key=getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    model_name="deepseek/deepseek-r1",
    callbacks=[input_display_callback, output_display_callback],
)
