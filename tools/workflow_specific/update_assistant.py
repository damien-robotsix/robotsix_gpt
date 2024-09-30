import os
import json
import sys
from openai import OpenAI
from generate_repo_structure import generate_structure_from_path


def main():
    """
    Updates assistant instructions based on the repository structure.
    """
    # Set up your OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    # Dynamically determine the repository path
    repo_path = os.getcwd()

    # Generate the repository structure
    structure = generate_structure_from_path(repo_path)

    # Load assistant ID from the assistant_config.json file
    config_file = os.path.join(repo_path, "repo_assistant_config.json")
    with open(config_file) as f:
        config = json.load(f)
    assistant_id = config.get("repo_assistant_id")

    # Get the directory name
    branch_name = sys.argv[1] if len(sys.argv) > 1 else "main"
    repo_name = os.path.basename(repo_path)

    # Prepare the update for the assistant's instructions
    new_instructions = f"Your role is to perform answer question about the {repo_name} repository on branch {branch_name}. You have access to all the files available in the repository in your database. When asked a question you MUST look in your database to answer precisely the question.\nRepository structure :\n{structure}"

    response = client.beta.assistants.update(
        assistant_id=assistant_id,
        instructions=new_instructions,
    )

    if response.id == assistant_id:
        print("Assistant instructions updated successfully.")
    else:
        print("Failed to update the assistant.")


if __name__ == "__main__":
    main()
