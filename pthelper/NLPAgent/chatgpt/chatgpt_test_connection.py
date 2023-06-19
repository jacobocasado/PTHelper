from rich.console import Console
import openai

from NLPAgent.chatgpt.chatgpt_api import ChatGPTAPI
from NLPAgent.chatgpt.config import ChatGPTConfig


def main():
    console = Console()
    chatgpt_config = ChatGPTConfig()

    # 3. test the connection for chatgpt api with GPT-3.5
    print("#### Test connection for OpenAI api (GPT-3.5)")
    try:
        chatgpt_config.model = "gpt-3.5-turbo"
        chatgpt = ChatGPTAPI(chatgpt_config)
        openai.api_key = chatgpt_config.openai_key
        result, conversation_id = chatgpt.send_new_message("Hi how are you?")
        console.print(
            "You're connected with OpenAI API. You have GPT-3.5 access. To start PentestGPT, please use <pentestgpt --reasoning_model=gpt-3.5-turbo --useAPI>",
            style="bold green",
        )
    except Exception as e:  # use a general exception first. Update later for debug
        #logger.error(e)
        console.print(
            "The OpenAI API key is not properly configured. Please follow README to update OpenAI API key through `export OPENAI_KEY=<>`",
            style="bold red",
        )
        print("The error is below:", e)


if __name__ == "__main__":
    main()