from dataclasses import dataclass
from enum import Enum
from typing import Optional

import openai
import tiktoken

from bot.utilities.logging import get_logger

logger = get_logger(__name__)


TOKENIZER = "cl100k_base"


class OpenAIChatModel(Enum):
    GPT_3_5 = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"


TOKEN_LIMITS = {
    OpenAIChatModel.GPT_3_5: 4000,
    OpenAIChatModel.GPT_4: 8000,
}


class Role(Enum):
    SYSTEM: str = "system"
    USER: str = "user"
    ASSISTANT: str = "assistant"


@dataclass
class Message:
    role: Role
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role.value, "content": self.content}


@dataclass
class Usage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class Completion:
    message: Message
    finish_reason: str
    index: int


@dataclass
class OpenAIChatResponse:
    created: int
    finish_reason: str
    model: str
    usage: Usage
    history: list[Message]
    prompt: str
    cut_prompt: str
    content: str


@dataclass(frozen=True)
class ConversationStatus:
    id: str
    object: str
    created: int
    model: str
    usage: Usage
    completion: Completion


class OpenAIConversation:
    def __init__(
        self,
        api_key: str,
        model: OpenAIChatModel = OpenAIChatModel.GPT_3_5,
        system_prompt: str | None = None,
    ):
        self._api_key = api_key
        self.model = model
        self._chat_history: list[Message] = []
        self._system_prompt = system_prompt or ""
        # TODO: Register total API usage and costs

    def _add_message(self, role: Role, content: str) -> None:
        self._chat_history.append(Message(role=role, content=content))

    def _get_system_prompt_message(self) -> str:
        return Message(role=Role.SYSTEM, content=self._system_prompt)

    def _get_tokenizer(self) -> tiktoken.Encoding:
        return tiktoken.get_encoding(TOKENIZER)

    def _compose_response(
        self, response: dict, prompt: str, cut_prompt: str
    ) -> OpenAIChatResponse:
        choice = response["choices"][0]
        return OpenAIChatResponse(
            created=response["created"],
            finish_reason=choice["finish_reason"],
            model=response["model"],
            usage=response["usage"],
            history=self._chat_history.copy(),
            prompt=prompt,
            cut_prompt=cut_prompt,
            content=choice["message"]["content"],
        )

    def get_text_token_length(
        self,
        text: list[Message],
        tokenizer: Optional[tiktoken.Encoding] = None,
    ) -> int:
        if tokenizer is None:
            tokenizer = self._get_tokenizer()
        return len(tokenizer.encode(text))

    def get_limit(self) -> int:
        return TOKEN_LIMITS[self.model]

    def preprocess_prompt(
        self,
        prompt: list[Message],
        allow_model_upgrade: bool = False,
        allow_message_removal: bool = True,
        allow_message_truncation: bool = True,
        tokenizer: Optional[tiktoken.Encoding] = None,
    ) -> tuple[list[Message], str]:
        if tokenizer is None:
            tokenizer = self._get_tokenizer()
        assert len(prompt) > 0, "The prompt must not be empty in order to preprocess it"
        assert (
            prompt[0].role == Role.SYSTEM
        ), "The first message must be the system prompt"

        if len(prompt) < 2:
            raise ValueError(
                "The prompt must contain at least 2 messages: system and user"
            )

        total_prompt_limit = self.get_limit()
        prompt_tokens = [
            self.get_text_token_length(message.content, tokenizer) for message in prompt
        ]
        total_prompt_length = sum(prompt_tokens)

        system_prompt_length = prompt_tokens[0]
        if system_prompt_length > total_prompt_limit:
            raise ValueError(
                f"The system prompt is too long, it must be less than {total_prompt_limit} tokens"
            )
        if total_prompt_length >= total_prompt_limit:
            if allow_model_upgrade and self.model == OpenAIChatModel.GPT_3_5:
                self.model = OpenAIChatModel.GPT_4
                logger.info("Upgrading model to GPT-4 to fit larger prompt")
                return self.preprocess_prompt(
                    prompt,
                    tokenizer,
                    False,
                    allow_message_removal,
                    allow_message_truncation,
                )

            if len(prompt) > 2 and allow_message_removal:
                # Elimitate the oldest message except the system prompt until the prompt fits
                prompt = prompt[0:1] + prompt[2:]
                logger.info(
                    "The prompt is too long, reducing the chat history to fit the limit"
                )
                return self.preprocess_prompt(
                    prompt,
                    tokenizer,
                    False,
                    allow_message_removal,
                    allow_message_truncation,
                )

            if len(prompt) == 2 and allow_message_truncation:
                # Reduce the user message until the prompt fits
                logger.warning(
                    "The prompt is too long, reducing the user message to fit the limit"
                )
                user_message = prompt[-1]
                user_limit = total_prompt_limit - system_prompt_length
                user_content = tokenizer.decode(
                    tokenizer.encode(user_message.content)[:user_limit]
                )
                cut_content = user_message.content[len(user_content) :]
                user_message = Message(role=user_message.role, content=user_content)
                return [prompt[0], user_message], cut_content

            raise ValueError(
                f"The prompt is too long, it must be less than {total_prompt_limit} tokens"
            )

        return prompt, ""

    def get_system_prompt(self) -> str:
        return self._system_prompt

    def set_system_prompt(self, system_prompt: str) -> None:
        self._system_prompt = system_prompt

    def get_chat_history(self) -> list[Message]:
        return self._get_system_prompt_message() + self._chat_history

    def get_completion(
        self,
        user_message: str,
        temperature: float = 0.7,
        allow_model_upgrade: bool = False,
        allow_message_removal: bool = True,
        allow_message_truncation: bool = True,
        system_prompt: str | None = None,
    ) -> OpenAIChatResponse:
        if system_prompt is not None:
            self.set_system_prompt(system_prompt)

        history = self.get_chat_history()
        new_message = Message(role=Role.USER, content=user_message)
        conversation_base_prompt = history + [new_message]

        conversation_prompt, cut_prompt = self.preprocess_prompt(
            conversation_base_prompt,
            allow_model_upgrade,
            allow_message_removal,
            allow_message_truncation,
        )

        response = openai.ChatCompletion.create(
            model=self.model,
            messages={message.to_dict() for message in conversation_prompt},
            temperature=temperature,
        )

        chat_response = self._compose_response(response, user_message, cut_prompt)
        self._add_message(Role.USER, user_message)
        self._add_message(Role.ASSISTANT, chat_response.content)

        return chat_response
