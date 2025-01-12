import sys
from .litellm_handler import LLMHandler, LlmConfig
from .agents.dispatcher import Dispatcher, DispatcherArgs


def main():
    if len(sys.argv) < 2:
        print("Please provide a prompt.")
        return
    user_prompt = sys.argv[1]
    config = LlmConfig(model="gpt-4o")
    llm_handler = LLMHandler(config)
    messages = [{"role": "user", "content": user_prompt}]
    dispatcher_args = DispatcherArgs(messages=messages)
    dispatcher = Dispatcher(llm_handler, dispatcher_args)
    _ = dispatcher.trigger()


if __name__ == "__main__":
    main()
