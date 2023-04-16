import openai
from typing import Optional
import tiktoken


class Summarizer:
    GPT_35_LIMIT = 4000
    GPT_4_LIMIT = 8000
    WORDS_LIMIT_ADDENDUM = " and less than {words_limit} words"
    SYSTEM_PROMPT = "You are a helpful assistant that generates summaries of texts extracted from PDF files or webpages."
    PROMPT_STRUCTURE = """Generate an executive summary of the text in the following format{words_limit_text}:
Subject: [theme]
Key points:
- ...

The text is:
{text}
"""

    def __init__(self, api_key: str, allow_gpt4: bool = True) -> None:
        self._api_key = api_key
        self._allow_gpt4 = allow_gpt4

    def _get_tokenizer(self) -> tiktoken.Encoding:
        return tiktoken.get_encoding("cl100k_base")

    def _get_base_prompt(
        self,
        text: str,
        words_limit: Optional[int] = None,
    ) -> str:
        words_limit_text = (
            ""
            if words_limit is None
            else self.WORDS_LIMIT_ADDENDUM.format(words_limit=words_limit)
        )
        return self.PROMPT_STRUCTURE.format(
            words_limit_text=words_limit_text, text=text
        )

    def _decide_model(self, base_prompt: str) -> tuple[str, str]:
        tokenizer = self._get_tokenizer()
        tokenized_system_prompt_length = len(tokenizer.encode(self.SYSTEM_PROMPT))
        tokenized_base_prompt_length = len(tokenizer.encode(base_prompt))
        total_length = tokenized_system_prompt_length + tokenized_base_prompt_length

        if total_length <= self.GPT_35_LIMIT:
            return base_prompt, "gpt-3.5-turbo"
        elif total_length <= self.GPT_4_LIMIT and self._allow_gpt4:
            return base_prompt, "gpt-4"
        else:
            # Reduce the prompt to fit the limit
            limit = self.GPT_4_LIMIT if self._allow_gpt4 else self.GPT_35_LIMIT
            message_limit = limit - tokenized_system_prompt_length
            model = "gpt-4" if self._allow_gpt4 else "gpt-3.5-turbo"
            prompt = tokenizer.decode(tokenizer.encode(base_prompt)[:message_limit])
            return prompt, model

    def _get_chat_completion(
        self,
        model: str,
        system_prompt: str,
        message: str,
        temperature: float,
    ) -> openai.ChatCompletion:
        openai.api_key = self._api_key
        return openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            temperature=temperature,
        )

    def generate_summary(
        self,
        text: str,
        words_limit: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str:
        base_prompt = self._get_base_prompt(text, words_limit)

        message, model = self._decide_model(base_prompt)

        response = self._get_chat_completion(
            model=model,
            system_prompt=self.SYSTEM_PROMPT,
            message=message,
            temperature=temperature,
        )

        return response.choices[0].message["content"]
