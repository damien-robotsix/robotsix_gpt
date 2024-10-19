from openai import OpenAI
import os
from typing import List, Dict
from embedding_search import search

api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

class AssistantFSMFunctions:
    def __init__(self, client):
        self.client = client

    def generate_context(self, prompt: str) -> List[Dict]:
        context = search(prompt)
        formatted_context = []

        for _, row in context.iterrows():
            line_start = row['line_start']
            line_end = row['line_end']
            file_path = row['file_path']
            with open(file_path, 'r') as file:
                lines = file.readlines()
                # Append with line numbers
                lines = [f"{i+1}: {line}" for i, line in enumerate(lines)]
                content = ''.join(
                    lines[line_start - 1:line_end]).strip()
            formatted_context.append({
                "file_path": file_path,
                "extracted_content": content
            })

        return formatted_context

    def respond_to_prompt(self, prompt: str) -> str:
        messages = [
            {
                "role": "user",
                "content": prompt
            },
            {
                "role": "user",
                "content": "Some context that might help you is found below:"
            }
        ]

        context = self.generate_context(prompt)

        for ctx in context:
            messages.append({
                "role": "user",
                "content": ctx["extracted_content"]
            })

        response = self.client.chat.completions.create(
            messages=messages,
            model="gpt-4o-2024-08-06"
        )

        return response.choices[0].message.content
