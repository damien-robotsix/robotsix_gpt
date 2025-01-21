from .graphs.dispatcher import DispatcherGraph
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
    while True:
        user_input = input("User: ")
        graph.invoke({"messages": [("user", user_input)]}, {"repo_path": repo_root})


if __name__ == "__main__":
    main()
