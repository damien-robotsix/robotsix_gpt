import sys
from .utils.configurations import RsgptConfig
from .utils.litellm_handler import LLMHandler
from .utils.context import RsgptContext
from .agents.dispatcher import Dispatcher, DispatcherArgs
from .utils.repo_chunker import update_chunks
from .utils.embeddings import update_embeddings


def main():
    if len(sys.argv) < 2:
        print("Please provide a prompt.")
        return
    user_prompt = sys.argv[1]
    context = RsgptContext()
    context.generate_context()
    config = RsgptConfig()
    config.load_config(context)

    if context.git_repo_root:
        update_chunks(config, context)
        update_embeddings(context)

    messages = [{"role": "user", "content": user_prompt}]
    dispatcher_args = DispatcherArgs(messages=messages)
    dispatcher = Dispatcher(LLMHandler(config.llm_config), dispatcher_args)
    _ = dispatcher.trigger()


if __name__ == "__main__":
    main()
