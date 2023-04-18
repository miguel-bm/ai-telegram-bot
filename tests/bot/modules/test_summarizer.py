import pytest
from unittest.mock import Mock, MagicMock
from bot.modules.openai_conversation import OpenAIConversation
from bot.modules.summarizer import Summarizer


@pytest.fixture
def conversation():
    return Mock(spec=OpenAIConversation)


@pytest.fixture
def summarizer(conversation: OpenAIConversation) -> Summarizer:
    return Summarizer(conversation)


def test_get_user_message_initial_prompt(summarizer: Summarizer):
    text = "This is a sample text."
    words_limit = 50
    message = summarizer._get_user_message(text, words_limit)
    expected_message = (
        "Generate an executive summary of the text in the following format and less than 50 words:\n"
        "Subject: [theme]\n"
        "Key points:\n"
        "- ...\n\n"
        "The text is:\n"
        "This is a sample text.\n"
    )
    assert message == expected_message


def test_get_user_message_recursive_prompt(summarizer: Summarizer):
    text = "This is a sample text."
    words_limit = 50
    previous_summary = "Subject: Sample\nKey points:\n- Point 1"
    message = summarizer._get_user_message(text, words_limit, previous_summary)
    expected_message = (
        "\n"
        "You have generated the following summary from the beginning of a text to summarize:\n"
        "Subject: Sample\nKey points:\n- Point 1\n\n"
        "Now, generate more key points for the next part of text in the following format and less than 50 words:\n"
        "- ...\n\n"
        "The next part of text is: This is a sample text.\n"
    )
    assert message == expected_message


def test_process_summary(summarizer: Summarizer):
    summary = "Some unrelated text. Subject: Test\nKey points:\n- Point 1"
    cut_from = "Subject:"
    processed_summary = summarizer._process_summary(summary, cut_from)
    expected_summary = "Subject: Test\nKey points:\n- Point 1"
    assert processed_summary == expected_summary


def test_generate_summary(
    monkeypatch: MagicMock, conversation: OpenAIConversation, summarizer: Summarizer
):
    text = "This is a sample text."
    words_limit = 50
    temperature = 0.7
    user_message = (
        "Generate an executive summary of the text in the following format and less than 50 words:\n"
        "Subject: [theme]\n"
        "Key points:\n"
        "- ...\n\n"
        "The text is:\n"
        "This is a sample text.\n"
    )

    completion = Mock()
    completion.content = "Subject: Sample\nKey points:\n- Point 1"
    completion.cut_prompt = None

    monkeypatch.setattr(
        conversation, "get_completion", lambda *args, **kwargs: completion
    )
    summary = summarizer.generate_summary(text, words_limit, temperature)
    expected_summary = "Subject: Sample\nKey points:\n- Point 1"

    assert summary == expected_summary
