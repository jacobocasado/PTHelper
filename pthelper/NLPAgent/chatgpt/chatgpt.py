# -*- coding: utf-8 -*-

import dataclasses
import json
import re
import time
import requests
import openai

from pathlib import Path
from typing import Dict, List
from uuid import uuid1

from NLPAgent.chatgpt.config import ChatGPTConfig





if __name__ == "__main__":
    chatgpt_config = ChatGPTConfig()
    chatgpt = ChatGPT(chatgpt_config)
    text, conversation_id = chatgpt.send_new_message(
        "I am a new tester for RESTful APIs."
    )
    print(text, conversation_id)
    result = chatgpt.send_message(
        "generate: {'post': {'tags': ['pet'], 'summary': 'uploads an image', 'description': '', 'operationId': 'uploadFile', 'consumes': ['multipart/form-data'], 'produces': ['application/json'], 'parameters': [{'name': 'petId', 'in': 'path', 'description': 'ID of pet to update', 'required': True, 'type': 'integer', 'format': 'int64'}, {'name': 'additionalMetadata', 'in': 'formData', 'description': 'Additional data to pass to server', 'required': False, 'type': 'string'}, {'name': 'file', 'in': 'formData', 'description': 'file to upload', 'required': False, 'type': 'file'}], 'responses': {'200': {'description': 'successful operation', 'schema': {'type': 'object', 'properties': {'code': {'type': 'integer', 'format': 'int32'}, 'type': {'type': 'string'}, 'message': {'type': 'string'}}}}}, 'security': [{'petstore_auth': ['write:pets', 'read:pets']}]}}",
        conversation_id,
    )
    # logger.info(chatgpt.extract_code_fragments(result))
