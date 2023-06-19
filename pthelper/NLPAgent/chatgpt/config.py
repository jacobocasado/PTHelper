import dataclasses
from rich.console import Console
import os
import sys

@dataclasses.dataclass
class ChatGPTConfig:
    # if you're using chatGPT (not API), please use "text-davinci-002-render-sha"
    # if you're using API, you may configure based on your needs
    # model: str = "text-davinci-002-render-sha"
    model: str = "gpt-4-browsing"

    # set up the openai key
    openai_key = os.getenv("OPENAI_KEY", None)
    # set the user-agent below
    userAgent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"

    if openai_key is None:
        print("Your OPENAI_KEY is not set. Please set it in the environment variable.")

    error_wait_time: float = 20
    is_debugging: bool = False
    proxies: dict = dataclasses.field(
        default_factory=lambda: {
            "http": "",
            "https": "",
        }
    )