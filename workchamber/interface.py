from typing import Dict, List, Optional, Union

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from workchamber.core import ChamberAssistant


class RichChamberAssistant(ChamberAssistant):
    def __init__(self):
        super().__init__()
        self.console = Console()

    def select_context_options(self) -> Dict[str, Union[List[str], str]]:
        context_options = {}
        context_choice = Prompt.ask(
            "Would you like to include conversation context or codebase context? [conv/code/both/none]"
        )

        if context_choice in ["conv", "both"]:
            num_messages = Prompt.ask(
                "How many previous messages would you like to include as context?",
                default="all",
                convert=int,
                validator=lambda x: x > 0,
            )

            if num_messages != "all":
                context_options["context"] = self.get_conversation_messages()[
                    -num_messages:
                ]
            else:
                context_options["context"] = self.get_conversation_messages()

        if context_choice in ["code", "both"]:
            code_filepath = Prompt.ask(
                "Enter the relative path to the code file you want to include in the context:"
            )
            context_options["code_filepath"] = code_filepath

        return context_options

    def chat(self):
        self.console.print("[bold green]Welcome to Chamber Assistant![/bold green]")

        while True:
            user_message = Prompt.ask("[bold cyan]You[/bold cyan]")

            if user_message.lower() in {"exit", "quit"}:
                self.console.print("[bold red]Goodbye![/bold red]")
                break

            context_options = self.select_context_options()

            # Generate the response.
            response = self.generate_response(user_message, **context_options)

            # Add messages to the conversation.
            self.add_message(user_message, "user")
            self.add_message(response, "ai")

            self.console.print(f"[bold magenta]Assistant:[/bold magenta] {response}")
