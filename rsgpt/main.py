from .graphs.dispatcher import DispatcherGraph
from langgraph.graph import MessagesState
from .utils.git import get_repo_root


def pretty_print_stream_chunk(chunk):
    for node, updates in chunk.items():
        print(f"Update from node: {node}")
        if updates:
            if "messages" in updates:
                updates["messages"][-1].pretty_print()
            else:
                print(updates)

        print("\n")


def main():
    repo_root = get_repo_root()
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
