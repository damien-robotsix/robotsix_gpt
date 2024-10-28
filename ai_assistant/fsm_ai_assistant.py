from openai import OpenAI
import os
import json
from ai_assistant.assistant_functions import AssistantFSMFunctions
from transitions import Machine
from ai_assistant.assistant_tools import TaskInput
import repo_chunker
import update_embedding
from pydantic import BaseModel

class ContextToDiscard(BaseModel):
    discarded: list[str]

class AIAssistantFSM:
    states = ['init', 'waiting_for_user_input', 'processing', 'responding', 'using_tool']

    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.assistant_functions = AssistantFSMFunctions(self.client)
        self.machine = Machine(
            model=self, states=AIAssistantFSM.states, initial='init')

        self.machine.add_transition(
            trigger='begin', source='init', dest='waiting_for_user_input')
        self.machine.add_transition(
            trigger='process_user_request', source='waiting_for_user_input', dest='processing')
        self.machine.add_transition(
            trigger='send_response', source='processing', dest='responding')
        self.machine.add_transition(
            trigger='use_tool', source='processing', dest='using_tool')

    def on_enter_waiting_for_user_input(self):
        user_input = input("Welcome to your AI Assistant! How can I assist you today?\n>>>: ")
        self.user_input = user_input
        self.context = self.assistant_functions.generate_context(user_input)
        self.process_user_request()

    def on_enter_processing(self):
        self.clean_context()
        response = self.assistant_functions.respond_to_prompt(self.user_input, self.context)
        self.current_response = response
        if response.choices[0].finish_reason == 'tool_calls':
            self.use_tool()
        else:
            print(response.choices[0].message)

    def clean_context(self):
        response = self.client.beta.chat.completions.parse(
            messages=[
                {"role": "system", "content": "You are tasked with determining which context elements can be discarded with respect to the user's request."},
                {"role": "user", "content": self.user_input},
                {"role": "user", "content": json.dumps(self.context)}
            ],
            model="gpt-4o-mini-2024-07-18",
            response_format=ContextToDiscard
        )

        discard_items = response.choices[0].message.parsed
        for item in discard_items.discarded:
            print(f"Discarding {item}")
            self.context.pop(item, None)  # Remove item from context

    def on_enter_using_tool(self):
        tool_calls = self.current_response.choices[0].message.tool_calls
        # Sort tool calls by line_start in descending order
        sorted_tool_calls = sorted(
            tool_calls,
            key=lambda tool: json.loads(
                tool.function.arguments).get('line_start', 0),
            reverse=True
        )
        for tool in sorted_tool_calls:
            if tool.function.name == 'AddContext':
                print("ADDING CONTEXT")
                arguments = json.loads(tool.function.arguments)
                self.context.update(self.assistant_functions.generate_context(
                    arguments['context_prompt']))
                self.process_user_request()
            else:
                task = TaskInput.model_construct(
                    input_type=tool.function.name, parameters=tool.function.arguments)
                feedback = task.execute()



if __name__ == "__main__":
    repo_chunker.main()
    update_embedding.main()
    assistant = AIAssistantFSM()
    assistant.begin()
