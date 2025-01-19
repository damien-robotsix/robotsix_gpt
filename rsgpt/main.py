from .graphs.specialist_with_memory import SpecialistWithMemoryGraph
from .graphs.repo_diver import RepoDiverGraph


def pretty_print_stream_chunk(chunk):
    for node, updates in chunk.items():
        print(f"Update from node: {node}")
        if "messages" in updates:
            updates["messages"][-1].pretty_print()
        else:
            print(updates)

        print("\n")


def main():
    # graph = SpecialistWithMemoryGraph("LangChain").compile()
    graph = RepoDiverGraph().compile()
    while True:
        user_input = input("User: ")

        for chunk in graph.stream({"messages": [("user", user_input)]}):
            pretty_print_stream_chunk(chunk)


if __name__ == "__main__":
    main()
