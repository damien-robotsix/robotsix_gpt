from langchain_openai import ChatOpenAI
from os import getenv, makedirs
import logging
from datetime import datetime
from langchain.callbacks.base import BaseCallbackHandler

# Setup logging directory and file
log_directory = ".rsgpt/log"
makedirs(log_directory, exist_ok=True)
log_filename = f"{log_directory}/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class InputDisplayCallbackHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        logging.info("--- INPUT SENT TO LLM ---")
        for prompt in prompts:
            logging.info(prompt)
        logging.info("-------------------------")


class OutputDisplayCallbackHandler(BaseCallbackHandler):
    def on_llm_end(self, response, **kwargs):
        logging.info("--- OUTPUT FROM LLM ---")
        logging.info(response)
        logging.info("-------------------------")


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
