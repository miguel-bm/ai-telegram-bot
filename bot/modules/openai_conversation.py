import openai
from dataclasses import dataclass
from enum import Enum
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


@dataclass
class Completion:
    message: Message
    finish_reason: str
    index: int


@dataclass
class ChatResponse:
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

    def _add_message(self, role: Role, content: str) -> None:
        self._chat_history.append(Message(role=role, content=content))

    def _get_system_prompt_message(self) -> str:
        return Message(role=Role.SYSTEM, content=self._system_prompt)

    def get_system_prompt(self) -> str:
        return self._system_prompt

    def set_system_prompt(self, system_prompt: str) -> None:
        self._system_prompt = system_prompt

    def get_chat_history(self) -> list[Message]:
        return self._get_system_prompt_message() + self._chat_history

    def _get_tokenizer(self) -> tiktoken.Encoding:
        return tiktoken.get_encoding(TOKENIZER)

    def _parse_response(self, response: dict) -> ChatResponse:
        choice = response["choices"][0]
        message = Message(
            role=choice["message"]["role"], content=choice["message"]["content"]
        )
        return ChatResponse(
            id=response["id"],
            object=response["object"],
            created=response["created"],
            model=response["model"],
            usage=response["usage"],
            completion=Completion(
                message=message,
                finish_reason=choice["finish_reason"],
                index=choice["index"],
            ),
        )

    def _preprocess_prompt(
        self,
        prompt: list[Message],
        tokenizer: tiktoken.Encoding,
        allow_model_upgrade: bool = False,
        allow_message_removal: bool = True,
        allow_message_truncation: bool = True,
    ) -> list[Message]:
        assert len(prompt) > 0, "The prompt must not be empty in order to preprocess it"
        assert (
            prompt[0].role == Role.SYSTEM
        ), "The first message must be the system prompt"

        if len(prompt) < 2:
            raise ValueError(
                "The prompt must contain at least 2 messages: system and user"
            )

        total_limit = TOKEN_LIMITS[self.model]
        prompt_tokens = [tokenizer.encode(m.content) for m in prompt]
        system_tokens = prompt_tokens[0]
        if system_tokens > total_limit:
            raise ValueError(
                f"The system prompt is too long, it must be less than {total_limit} tokens"
            )

        total_length = sum(prompt_tokens)
        if total_length >= total_limit:
            if allow_model_upgrade and self.model == OpenAIChatModel.GPT_3_5:
                self.model = OpenAIChatModel.GPT_4
                logger.info("Upgrading model to GPT-4 to fit larger prompt")
                return self._preprocess_prompt(prompt, allow_model_upgrade=False)

            if len(prompt) > 2 and allow_message_removal:
                # Elimitate the oldest message except the system prompt until the prompt fits
                prompt = prompt[0:1] + prompt[2:]
                logger.info(
                    "The prompt is too long, reducing the chat history to fit the limit"
                )
                return self._preprocess_prompt(prompt, tokenizer, False)

            if len(prompt) == 2 and allow_message_truncation:
                # Reduce the user message until the prompt fits
                logger.warning(
                    "The prompt is too long, reducing the user message to fit the limit"
                )
                user_message = prompt[-1]
                user_limit = total_limit - system_tokens
                user_content = tokenizer.decode(
                    tokenizer.encode(user_message.content)[:user_limit]
                )
                user_message = Message(role=user_message.role, content=user_content)
                return self._preprocess_prompt(
                    [prompt[0], user_message], tokenizer, False
                )

            raise ValueError(
                f"The prompt is too long, it must be less than {total_limit} tokens"
            )

        return prompt

    def get_completion(
        self,
        user_message: str,
        temperature: float = 0.7,
        allow_model_upgrade: bool = False,
        system_prompt: str | None = None,
    ) -> ChatResponse:
        if system_prompt is not None:
            self.set_system_prompt(system_prompt)

        tokenizer = self._get_tokenizer()
        history = self.get_chat_history()
        new_message = Message(role=Role.USER, content=user_message)
        conversation_base_prompt = history + [new_message]

        conversation_prompt = self._preprocess_prompt(
            conversation_base_prompt, tokenizer, allow_model_upgrade
        )

        response = openai.ChatCompletion.create(
            model=self.model,
            messages={message.to_dict() for message in conversation_prompt},
            temperature=temperature,
        )

        chat_response = self._parse_response(response)
        self._add_message(Role.USER, user_message)
        self._add_message(Role.ASSISTANT, chat_response.completion.message.content)

        return chat_response
