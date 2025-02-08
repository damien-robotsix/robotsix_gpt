from .graphs.dispatcher import DispatcherGraph
from .graphs.commit_assistant import CommitAssistantGraph
from langgraph.graph import MessagesState
from .utils.git import get_repo_root
import argparse


def main():
    parser = argparse.ArgumentParser(description="Run RSgpt with optional file input or commit mode.")
    parser.add_argument(
        "--commit", action="store_true", help="Run commit assistant mode."
    )
    parser.add_argument(
        "--file", type=str, help="Provide the initial input through a file."
    )
    args = parser.parse_args()

    repo_root = get_repo_root()
    graph = DispatcherGraph().compile()
    messages = MessagesState()

    if args.file:
        try:
            with open(args.file, 'r') as file:
                initial_input = file.read()
            messages["messages"] = [("user", initial_input)]
            messages = graph.invoke(
                messages, {"repo_path": repo_root, "recursion_limit": 100}
            )
            messages["messages"][-1].pretty_print()
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found.")

    if args.commit:
        graph = CommitAssistantGraph().compile()
        messages["messages"] = []
        messages = graph.invoke(messages, {"repo_path": repo_root})
    else:
        if not args.file:
            messages["messages"] = []
        while True:
            user_input = input("User: ")
            messages["messages"].append(("user", user_input))
            messages = graph.invoke(
                messages, {"repo_path": repo_root, "recursion_limit": 100}
            )
            messages["messages"][-1].pretty_print()


if __name__ == "__main__":
    main()
