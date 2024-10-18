from transitions import Machine


class AIAssistantFSM:
    states = ['init', 'waiting_for_user_input', 'processing', 'responding']

    def __init__(self):
        self.machine = Machine(
            model=self, states=AIAssistantFSM.states, initial='init')

        self.machine.add_transition(
            trigger='process_request', source='waiting_for_user_input', dest='processing')
        self.machine.add_transition(
            trigger='send_response', source='processing', dest='responding')
        self.machine.add_transition(
            trigger='begin', source='init', dest='waiting_for_user_input')

    def on_enter_waiting_for_user_input(self):
        user_input = input(
            ">>>: ")

    def on_enter_responding(self):
        print("Sending response to user.")

    def on_enter_idle(self):
        print("Returning to idle state.")


if __name__ == "__main__":
    assistant = AIAssistantFSM()
    assistant.begin()
