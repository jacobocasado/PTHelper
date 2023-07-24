import openai  # pip install openai
from config.pthelper_config import agent_config
from pthelper.nlpagent.agent.chatgpt.chatgpt_api import ChatGPTAPI
from pthelper.nlpagent.prompts.prompts import NLPAgentPrompt


class NLPAgent:

    def __new__(cls, mode):
        # A dictionary to map different scanning modes to respective classes
        nlpagent_classes = {
            "chatgpt": ChatGPTAPIAgent
            # For future nlpagent modes, add the user-defined flag and the corresponding child class name here
        }
        # Get the scanner_class from the dictionary, default is scanner itself
        nlpagent_class = nlpagent_classes.get(mode, NLPAgent)
        return super(NLPAgent, cls).__new__(nlpagent_class)

    def __init__(self, mode):
        self.mode = mode

    def process(self, basic_context):
        print(f"[AGENT] Starting...")

# Children class that uses ChatGPT agent with ChatGPTAPI library as the NLPAgent type.
# This is the first NLPAgent type available.
class ChatGPTAPIAgent(NLPAgent):

    def __init__(self, mode):
        super().__init__(mode)
        # Initialize ChatGPTAPI
        self.api = ChatGPTAPI()
        openai.api_key = agent_config.OPENAI_API_KEY

    def cve_summary(self,port_context):
        response, conversation_id = self.api.start_conversation_with_context(NLPAgentPrompt.generation_session_init)
        response = self.api.send_message(str(port_context), conversation_id)
        print(response)
    def process(self, context):
        self.cve_summary(context)