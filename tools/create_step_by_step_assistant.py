import os
from assistant_gpt import StepByStepOutput
from openai import OpenAI

# Define the assistant's name and instructions
name = f"Step-by-Step Assistant"
instructions = """
Convert the input text into a step-by-step json output.
"""

# Set your OpenAI API key
api_key = os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>")
client = OpenAI(api_key=api_key)

# Create the assistant
response = client.beta.assistants.create(
    name=name,
    instructions=instructions,
    model="gpt-4o-mini-2024-07-18",
)

# Extract the assistant ID
assistant_id = response.id

format = {"type": "json_schema", "json_schema": {
    "name": "StepByStepOutput",
    "schema": StepByStepOutput.model_json_schema(),
    "strict": True
    }
}
format["json_schema"]["schema"]["additionalProperties"] = False
client.beta.assistants.update(
    assistant_id=assistant_id,
    response_format=format
)
