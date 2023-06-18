import json
import os
from typing import Dict, List, Optional, Union
import openai


# Conversation class
class Conversation:
    def __init__(self):
        self.messages = []

    def add_message(self, message: str, sender: str):
        self.messages.append({"sender": sender, "message": message})

    def get_messages(self) -> List[str]:
        return [message["message"] for message in self.messages]


# Codebase class
class Codebase:
    def __init__(self, path: str):
        self.path = os.path.abspath(path)
        self.files: Dict[str, str] = {}

    def load_files(self):
        for root, _, filenames in os.walk(self.path):
            for filename in filenames:
                if filename.endswith(".py"):
                    file_path = os.path.join(root, filename)
                    with open(file_path, "r") as file:
                        self.files[file_path] = file.read()


# ChamberAssistant class
class ChamberAssistant:
    def __init__(self, storage_path="conversations", api_key=None):
        self.conversations: Dict[str, Conversation] = {}
        self.active_conversation_name: Optional[str] = None
        self.codebase: Codebase = None
        self.storage_path = storage_path
        self.api_key = api_key
        os.makedirs(storage_path, exist_ok=True)
        self.load_conversations()

    def load_conversations(self):
        for filename in os.listdir(self.storage_path):
            if filename.endswith(".json"):
                conversation_name = filename[:-5]
                filepath = os.path.join(self.storage_path, filename)
                with open(filepath, "r") as file:
                    messages = json.load(file)
                conversation = Conversation()
                conversation.messages = messages
                self.conversations[conversation_name] = conversation

    def save_conversation(self, name: str):
        filepath = os.path.join(self.storage_path, f"{name}.json")
        with open(filepath, "w") as file:
            json.dump(self.conversations[name].messages, file)

    def new_conversation(self, name: str):
        if name not in self.conversations:
            self.conversations[name] = Conversation()
        self.active_conversation_name = name

    def add_message(self, message: str, sender: str):
        if not self.active_conversation_name:
            raise ValueError(
                "No active conversation. Please create one using 'new_conversation()' method."
            )
        self.conversations[self.active_conversation_name].add_message(message, sender)
        self.save_conversation(self.active_conversation_name)

    def get_conversation_messages(self) -> List[str]:
        if not self.active_conversation_name:
            return []
        return self.conversations[self.active_conversation_name].get_messages()

    def load_codebase(self, path: str):
        self.codebase = Codebase(path)
        self.codebase.load_files()

    def select_context_options(self) -> Dict[str, Union[List[str], str]]:
        context_options = {}
        context_choice = input(
            "Would you like to include conversation context or codebase context? [conv/code/both/none] "
        )

        if context_choice in ["conv", "both"]:
            num_messages = input(
                "How many previous messages would you like to include as context? (enter 'all' for all messages) "
            )
            num_messages = int(num_messages) if num_messages.isdigit() else num_messages

            if num_messages != "all":
                context_options["context"] = self.get_conversation_messages()[
                    -num_messages:
                ]
            else:
                context_options["context"] = self.get_conversation_messages()

        if context_choice in ["code", "both"]:
            code_filepath = input(
                "Enter the relative path to the code file you want to include in the context: "
            )
            context_options["code_filepath"] = code_filepath

        return context_options

    def generate_response(
        self,
        query: str,
        context: Union[List[str], str] = None,
        code_filepath: str = None,
    ):
        openai.api_key = self.api_key

        # Build messages for conversation context
        messages = [{"role": "system", "content": "You are a helpful assistant."}]

        if context:
            for i in range(0, len(context) - 1, 2):
                messages.extend(
                    [
                        {"role": "user", "content": context[i]},
                        {"role": "assistant", "content": context[i + 1]},
                    ]
                )

        if code_filepath:
            code_context = self.codebase.files.get(code_filepath)
            if code_context:
                messages.append(
                    {
                        "role": "system",
                        "content": f"The user is working on the following code:\n{code_context}\n",
                    }
                )

        messages.append({"role": "user", "content": query})

        response = openai.ChatCompletion.create(model="gpt-4-32k", messages=messages)

        return response.choices[0].message["content"]


if __name__ == "__main__":
    # Usage:
    assistant = ChamberAssistant()
    assistant.load_codebase("../")
    assistant.new_conversation()

    # Sending a message
    assistant.add_message("What is the purpose of the Conversation class?", "user")

    # Generate a response with context and code_filepath
    response = assistant.generate_response(
        "Can you explain how to use the Codebase class?",
        context=assistant.get_conversation_messages(),
        code_filepath="path/to/specific/file.py",
    )

    # Add AI's response message
    assistant.add_message(response, "ai")
