import dataclasses
import os
import re
import time
from uuid import uuid1

import openai  # pip install openai
import requests
import typer  # pip install "typer[all]"
from rich import print  # pip install rich
from rich.table import Table
from rich.console import Console
from typing import Dict, List

from config.pthelper_config import pthelper_config
from nlpagent.agent.chatgpt.chatgpt_api import ChatGPTAPI
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

    def report(self):
        self.mode.report()

    def process(self, basic_context):
        print(f"[AGENT] Starting...")


# Children class that uses ChatGPT agent with ChatGPTAPI library as the NLPAgent type.
# This is the first NLPAgent type available.
class ChatGPTAPIAgent(NLPAgent):

    def __init__(self, mode):
        super().__init__(mode)
        # Initialize ChatGPTAPI
        self.api = ChatGPTAPI()
        openai.api_key = pthelper_config.OPENAI_API_KEY

    def cve_summary(self,port_context):
        self.api.start_conversation_with_context()

    def process(self, context):
        self.cve_summary(context)