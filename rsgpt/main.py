from .graphs.dispatcher import DispatcherGraph
from .graphs.commit_assistant import CommitAssistantGraph
from langgraph.graph import MessagesState
from .utils.git import get_repo_root
import argparse


def main():
    parser = argparse.ArgumentParser(description="Run RSgpt with optional commit mode.")
    parser.add_argument(
        "--commit", action="store_true", help="Run commit assistant mode."
    )
    args = parser.parse_args()

    repo_root = get_repo_root()

    if args.commit:
        graph = CommitAssistantGraph().compile()
        messages = MessagesState()
        messages["messages"] = []
        messages = graph.invoke(messages, {"repo_path": repo_root})
    else:
        graph = DispatcherGraph().compile()
        messages = MessagesState()
        messages["messages"] = []
        while True:
            user_input = input("User: ")
            messages["messages"].append(("user", user_input))
            messages = graph.invoke(messages, {"repo_path": repo_root})
            messages["messages"][-1].pretty_print()


if __name__ == "__main__":
    main()
