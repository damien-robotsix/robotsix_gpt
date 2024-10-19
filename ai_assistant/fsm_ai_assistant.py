from openai import OpenAI
import os
from ai_assistant.assistant_functions import AssistantFSMFunctions
from transitions import Machine
from ai_assistant.assistant_tools import TaskInput
import repo_chunker
import update_embedding

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
        user_input = input(">>>: ")
        self.process_user_request(user_input)

    def on_enter_processing(self, user_input):
        response = self.assistant_functions.respond_to_prompt(user_input)
        print(response.choices[0])
        self.current_response = response
        if response.choices[0].finish_reason == 'tool_calls':
            self.use_tool()

    def on_enter_using_tool(self):
        for tool in self.current_response.choices[0].message.tool_calls:
            print(tool)
            task = TaskInput.model_construct(
                input_type=tool.function.name, parameters=tool.function.arguments)
            output = task.execute()

    def on_enter_idle(self):
        print("Returning to idle state.")


if __name__ == "__main__":
    repo_chunker.main()
    update_embedding.main()
    assistant = AIAssistantFSM()
    assistant.begin()
