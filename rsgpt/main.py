import sys
from .litellm_handler import LLMHandler, LlmConfig
from .agents.dispatcher import Dispatcher


def main():
    if len(sys.argv) < 2:
        print("Please provide a prompt.")
        return
    user_prompt = sys.argv[1]
    config = LlmConfig(model="gpt-4o")
    llm_handler = LLMHandler(config)
    dispatcher = Dispatcher(llm_handler)
    result = dispatcher.trigger(user_prompt)
    print(result)


if __name__ == "__main__":
    main()
