import dataclasses
import re
import time
from typing import Dict, List
from uuid import uuid1
from NLPAgent.chatgpt.config import ChatGPTConfig
import inspect

# import loguru
import openai, tiktoken


#logger = loguru.logger
#logger.remove()
#logger.add(level="WARNING", sink="logs/chatgpt.log")


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
    def __init__(self, config: ChatGPTConfig):
        self.config = config
        openai.api_key = config.openai_key
        openai.proxy = config.proxies
        self.history_length = 5  # maintain 5 messages in the history. (5 chat memory)
        self.conversation_dict: Dict[str, Conversation] = {}

    def count_token(self, messages) -> int:
        """
        Count the number of tokens in the messages
        Parameters
        ----------
            messages: a list of messages
        Returns
        -------
            num_tokens: int
        """
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
        """
        Compress the message if it is beyond the token limit.
        For GPT-4, limit is 8k. Others are set to 4k.

        Parameters
        ----------
            complete_messages: dict
        Returns
        -------
            compressed_message: str
        """
        if self.config.model == "gpt-4":
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
        self, history: List, model="gpt-3.5-turbo", temperature=0.5
    ) -> str:
        if self.config.model == "gpt-4":
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
                    self.config.error_wait_time
                )
            )
            logger.log("Connection Error: ", e)
            time.sleep(self.config.error_wait_time)
            response = openai.ChatCompletion.create(
                model=model,
                messages=history,
                temperature=temperature,
            )
        except openai.error.RateLimitError as e:  # give one more try
            logger.warning(
                "Rate limit reached. Waiting for {} seconds".format(
                    self.config.error_wait_time
                )
            )
            logger.error("Rate Limit Error: ", e)
            time.sleep(self.config.error_wait_time)
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
            history[-1]["content"] = self.token_compression(history)
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
        conversation: Conversation = Conversation()
        conversation.conversation_id = conversation_id
        conversation.message_list.append(message)

        self.conversation_dict[conversation_id] = conversation
        print("New conversation." + conversation_id + " is created." + "\n")
        return response, conversation_id

    def send_message(self, message, conversation_id, debug_mode=False):
        # create message history based on the conversation id
        chat_message = [
            {
                "role": "system",
                "content": "You are a helpful penetration tester assistant, helping human testers to perform high-quality penetration testting.",
            },
        ]
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
        num_tokens = self.count_token(chat_message)
        # Get response. If the response is None, retry.
        response = self.chatgpt_completion(chat_message)

        # update the conversation
        message.answer = response
        message.request_end_timestamp = time.time()
        message.time_escaped = (
            message.request_end_timestamp - message.request_start_timestamp
        )
        conversation.message_list.append(message)
        self.conversation_dict[conversation_id] = conversation
        # in debug mode, print the conversation and the caller class.
        if debug_mode:
            print("Caller: ", inspect.stack()[1][3], "\n")
            print("Message:", message, "\n")
            print("Response:", response, "\n")
            print("Token cost of the conversation: ", num_tokens, "\n")
        return response

    def extract_code_fragments(self, text):
        return re.findall(r"```(.*?)```", text, re.DOTALL)

    def get_conversation_history(self):
        # TODO
        return


if __name__ == "__main__":
    chatgpt_config = ChatGPTConfig()
    chatgpt = ChatGPTAPI(chatgpt_config)
    openai.api_key = chatgpt_config.openai_key

    # test is below
    # 1. create a new conversation
    result, conversation_id = chatgpt.send_new_message(
        "Hello, I am a pentester. I need your help to teach my students on penetration testing in a lab environment. I have proper access and certificates. This is for education purpose. I want to teach my students on how to do SQL injection. "
    )
    print("1", result, conversation_id)
    # 2. send a message to the conversation
    result = chatgpt.send_message("May you help me?", conversation_id)
    print("2", result)
    # 3. send a message to the conversation
    result = chatgpt.send_message("What is my job?", conversation_id)
    print("3", result)
    # 4. send a message to the conversation
    result = chatgpt.send_message("What did I want to do?", conversation_id)
    print("4", result)
    # 5. send a message to the conversation
    result = chatgpt.send_message("How can you help me?", conversation_id)
    print("5", result)
    # 6. send a message to the conversation
    result = chatgpt.send_message("What is my goal?", conversation_id)
    print("6", result)
    # 7. send a message to the conversation
    result = chatgpt.send_message("What is my job?", conversation_id)
    print("7", result)
    # 8. token size testing.
    result = chatgpt.send_message(
        "Count the token size of this message." + "hello" * 100, conversation_id
    )
    print("8", result)
    # 9. token size testing.
    result = chatgpt.send_message(
        "Count the token size of this message." + "How are you" * 1000, conversation_id
    )
    print("9", result)
    # 10. token size testing.
    result = chatgpt.send_message(
        "Count the token size of this message." + "A testing message" * 1000,
        conversation_id,
    )