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

class NLPAgent:
    def __init__(self, mode):
        self.set_mode(mode)

    def set_mode(self, mode):
        ModeClass = self.mode_classes.get(mode)
        if ModeClass is None:
            raise ValueError(f'Unsupported mode: {mode}')
        self.mode = ModeClass()

    def report(self):
        self.mode.report()

    def process(self, basic_context):
        self.mode.process(basic_context)
