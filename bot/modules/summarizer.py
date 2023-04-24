from typing import Optional

from bot.modules.openai_conversation import OpenAIConversation
from bot.utilities.logging import get_logger

logger = get_logger(__name__)


class Summarizer:
    GPT_35_LIMIT = 4000
    GPT_4_LIMIT = 8000
    WORDS_LIMIT_ADDENDUM = " and less than {words_limit} words"
    SYSTEM_PROMPT = "You are a helpful assistant that generates summaries of texts extracted from PDF files or webpages."
    PROMPT = """Generate an executive summary of the text in the following format{words_limit_text}:
Subject: [theme]
Key points:
- [key point]
- ...

The text is:
{text}
"""

    RECURSIVE_PROMPT = """
You have generated the following summary from the beginning of a text to summarize:
{previous_summary}

Now, generate more new key points for the next part of text in the following format{words_limit_text}:
Key points:
- [key point]
- ...


The next part of text is: {text}
"""

    def __init__(
        self,
        allow_gpt4: bool = False,
        allow_recursion: bool = True,
    ) -> None:
        self._allow_gpt4 = allow_gpt4
        self._allow_recursion = allow_recursion

    def _get_user_message(
        self,
        text: str,
        words_limit: Optional[int] = None,
        previous_summary: Optional[str] = None,
    ) -> str:
        words_limit_text = self.WORDS_LIMIT_ADDENDUM.format(words_limit=words_limit)
        words_limit_text = "" if words_limit is None else words_limit_text
        if previous_summary is None:
            logger.info("Generating standard summary prompt")
            return self.PROMPT.format(
                words_limit_text=words_limit_text,
                text=text,
            )
        else:
            logger.info("Generating recursive summary prompt")
            return self.RECURSIVE_PROMPT.format(
                words_limit_text=words_limit_text,
                text=text,
                previous_summary=previous_summary,
            )

    def _process_summary(self, summary: str, cut_from: str) -> str:
        subject_index = summary.find(cut_from)
        if subject_index != -1:
            summary = summary[subject_index:]
        return summary

    def estimate_summary(
        self,
        text: str,
        words_limit: Optional[int] = None,
        previous_summary: Optional[str] = None,
    ) -> int:
        # TODO
        pass

    def generate_summary(
        self,
        text: str,
        words_limit: Optional[int] = None,
        temperature: float = 0.7,
        previous_summary: Optional[str] = None,
    ) -> str:
        conversation = OpenAIConversation(system_prompt=self.SYSTEM_PROMPT)
        user_message = self._get_user_message(text, words_limit, previous_summary)
        response = conversation.get_completion(
            user_message=user_message,
            temperature=temperature,
            allow_model_upgrade=self._allow_gpt4,
            allow_message_removal=True,
            allow_message_truncation=True,
        )

        if previous_summary:
            # Add the new part of summary to the previous one
            new_content = self._process_summary(response.content, cut_from="-")
            summary = previous_summary + "\n" + new_content
        else:
            summary = self._process_summary(response.content, cut_from="Subject:")

        cut_prompt = response.cut_prompt
        if cut_prompt and self._allow_recursion:
            # Recursively generate more key points for the next part of text
            logger.info("Recursively generating more key points")
            return self.generate_summary(
                cut_prompt,
                words_limit,
                temperature,
                previous_summary=summary,
            )
        return summary


if __name__ == "__main__":
    from bot.utilities.token import get_bot_token
    from pathlib import Path

    bot_token = get_bot_token()

    conv = OpenAIConversation(bot_token)
    # summarizer = Summarizer(conv, allow_gpt4=False, allow_recursion=True)
    path_to_text = Path("tests/assets/count.txt")
    text = path_to_text.read_text()
    text_section = text[:30000]

    tokens = conv.get_text_token_length(text_section)
    print(f"Text length: {tokens} tokens")

    summarizer = Summarizer(allow_gpt4=False, allow_recursion=True)
    summary = summarizer.generate_summary(
        text_section, words_limit=100, temperature=0.2
    )
    print(summary)
