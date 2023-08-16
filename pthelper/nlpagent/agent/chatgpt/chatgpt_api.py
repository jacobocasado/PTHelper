import dataclasses
import os
import re
import time
import inspect
import loguru
import openai, tiktoken

from typing import Dict, List
from uuid import uuid1
from config.pthelper_config import general_config, agent_config

logger = loguru.logger
logger.remove()
logger.add(level="WARNING", sink="logs/chatgpt.log")

@dataclasses.dataclass
class Message:
    ask_id: str = None
    ask: dict = None
    answer: dict = None
    answer_id: str = None
    request_start_timestamp: float = None
    request_end_timestamp: float = None
    time_escaped: float = None


@dataclasses.dataclass
class Conversation:
    conversation_id: str = None
    message_list: List[Message] = dataclasses.field(default_factory=list)

    def __hash__(self):
        return hash(self.conversation_id)

    def __eq__(self, other):
        if not isinstance(other, Conversation):
            return False
        return self.conversation_id == other.conversation_id


class ChatGPTAPI:
    def __init__(self):
        # openai.proxy = agent_config.CHATGPT_PROXIES
        self.history_length = agent_config.HISTORY_LENGTH
        self.conversation_dict: Dict[str, Conversation] = {}

    def count_token(self, messages) -> int:
        # count the token. Use model gpt-3.5-turbo-0301, which is slightly different from gpt-4
        # https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
        model = "gpt-3.5-turbo-0301"
        tokens_per_message = (
            4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        )
        tokens_per_name = -1  # if there's a name, the role is omitted
        encoding = tiktoken.encoding_for_model(model)
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens

    def token_compression(self, complete_messages) -> str:
        if agent_config.NLPAGENTMODEL == "gpt-4":
            token_limit = 8000
        else:
            token_limit = 4000
        if self.count_token(complete_messages) > token_limit:
            # send a separate API request to compress the message
            chat_message = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that helps to summarize messages.",
                },
                {
                    "role": "user",
                    "content": "Please reduce the word count of the given message to save tokens. Keep its original meaning so that it can be understood by a large language model.",
                },
            ]
            compressed_message = self.chatgpt_completion(chat_message)
            return compressed_message

        # if not compressed, return the last message
        raw_message = complete_messages[-1]["content"]
        return raw_message

    def chatgpt_completion(
        self, history: List, model="gpt-3.5-turbo", temperature=agent_config.TEMPERATURE
    ) -> str:
        if agent_config.NLPAGENTMODEL == "gpt-4":
            model = "gpt-4"
            # otherwise, just use the default model (because it is cheaper lol)
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=history,
                temperature=temperature,
            )
        except openai.error.APIConnectionError as e:  # give one more try
            logger.warning(
                "API Connection Error. Waiting for {} seconds".format(
                    agent_config.ERROR_WAIT_TIME
                )
            )
            logger.log("Connection Error: ", e)
            time.sleep(agent_config.ERROR_WAIT_TIME)
            response = openai.ChatCompletion.create(
                model=model,
                messages=history,
                temperature=temperature,
            )
        except openai.error.RateLimitError as e:  # give one more try
            logger.warning(
                "Rate limit reached. Waiting for {} seconds".format(
                    agent_config.ERROR_WAIT_TIME
                )
            )
            logger.error("Rate Limit Error: ", e)
            time.sleep(agent_config.ERROR_WAIT_TIME)
            response = openai.ChatCompletion.create(
                model=model,
                messages=history,
                temperature=temperature,
            )
        except openai.error.InvalidRequestError as e:  # token limit reached
            logger.warning("Token size limit reached. The recent message is compressed")
            logger.error("Token size error; will retry with compressed message ", e)
            # compress the message in two ways.
            ## 1. compress the last message
            # history[-1]["content"] = self.token_compression(history)
            ## 2. reduce the number of messages in the history. Minimum is 2
            if self.history_length > 2:
                self.history_length -= 1
            ## update the history
            history = history[-self.history_length :]
            response = openai.ChatCompletion.create(
                model=model,
                messages=history,
                temperature=temperature,
            )

        # if the response is a tuple, it means that the response is not valid.
        if isinstance(response, tuple):
            logger.warning("Response is not valid. Waiting for 5 seconds")
            try:
                time.sleep(5)
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=history,
                    temperature=temperature,
                )
                if isinstance(response, tuple):
                    logger.error("Response is not valid. ")
                    raise Exception("Response is not valid. ")
            except Exception as e:
                logger.error("Response is not valid. ", e)
                raise Exception(
                    "Response is not valid. The most likely reason is the connection to OpenAI is not stable. "
                    "Please doublecheck with `pentestgpt-connection`"
                )
        return response["choices"][0]["message"]["content"]

    # Method to start a new conversation with an attached context as parameter.
    # Contexts are defined in the prompts file in the "prompts" folder.
    def start_conversation_with_context(self, context=None):
        start_time = time.time()
        # Add the context to the conversation.
        history = [{
                "role": "system",
                "content": context,
            }]
        message: Message = Message()
        message.ask_id = str(uuid1())
        message.ask = context
        message.request_start_timestamp = start_time
        response = self.chatgpt_completion(history)
        message.answer = response
        message.request_end_timestamp = time.time()
        message.time_escaped = (
                message.request_end_timestamp - message.request_start_timestamp
        )

        # create a new conversation with a new uuid
        conversation_id = str(uuid1())
        with open(general_config.CONVERSATIONFILE, "w") as file:
            file.write(conversation_id)
        conversation: Conversation = Conversation()
        conversation.conversation_id = conversation_id
        conversation.message_list.append(message)

        self.conversation_dict[conversation_id] = conversation
        # Return the response given by chatgpt and the conversation ID.
        return response, conversation_id

    # UNUSED: Method to send a new message without context. Starts a new conversation.
    def send_new_message(self, message):
        # create a message
        start_time = time.time()
        data = message
        history = [{"role": "user", "content": data}]
        message: Message = Message()
        message.ask_id = str(uuid1())
        message.ask = data
        message.request_start_timestamp = start_time
        response = self.chatgpt_completion(history)
        message.answer = response
        message.request_end_timestamp = time.time()
        message.time_escaped = (
            message.request_end_timestamp - message.request_start_timestamp
        )

        # create a new conversation with a new uuid
        conversation_id = str(uuid1())
        with open(agent_config.CONVERSATIONFILE, "w") as file:
            file.write(conversation_id)
        conversation: Conversation = Conversation()
        conversation.conversation_id = conversation_id
        conversation.message_list.append(message)

        self.conversation_dict[conversation_id] = conversation
        return response, conversation_id

    # Method to send a message TO A GIVEN CONVERSATION, which has context.
    # Used to give the inputs to chatgpt AFTER giving the prompts.
    def send_message(self, message, conversation_id, debug_mode=False):
        # create message history based on the conversation id
        chat_message = []
        data = message
        conversation = self.conversation_dict[conversation_id]
        for message in conversation.message_list[-self.history_length :]:
            chat_message.extend(
                (
                    {"role": "user", "content": message.ask},
                    {"role": "assistant", "content": message.answer},
                )
            )
        # append the new message to the history
        chat_message.append({"role": "user", "content": data})
        # create the message object
        message: Message = Message()
        message.ask_id = str(uuid1())
        message.ask = data
        message.request_start_timestamp = time.time()
        # count the token cost
        # num_tokens = self.count_token(chat_message)
        # Get response. If the response is None, retry.
        response = self.chatgpt_completion(chat_message)

        # update the conversation
        message.answer = response
        message.request_end_timestamp = time.time()
        message.time_escaped = (
            message.request_end_timestamp - message.request_start_timestamp
        )
        conversation.message_list.append(message)
        conversation = self.conversation_dict[conversation_id]
        self.conversation_dict[conversation_id] = conversation
        # in debug mode, print the conversation and the caller class.
        if debug_mode:
            print("Caller: ", inspect.stack()[1][3], "\n")
            print("Message:", message, "\n")
            print("Response:", response, "\n")
        return response

    def extract_code_fragments(self, text):
        return re.findall(r"```(.*?)```", text, re.DOTALL)

    def get_conversation_history(self):
        # TODO
        return