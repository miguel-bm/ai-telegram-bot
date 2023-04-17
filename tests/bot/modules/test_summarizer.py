import unittest
from unittest.mock import patch, MagicMock
from bot.modules.summarizer import Summarizer


class TestSummarizer(unittest.TestCase):
    def setUp(self):
        self.summarizer = Summarizer(api_key="dummy_key")

    @patch("bot.modules.summarizer.openai.ChatCompletion.create")
    def test_generate_summary(self, mock_create):
        mock_create.return_value.choices = [
            MagicMock(message={"content": "This is a summary."})
        ]

        text = "This is the text."
        expected_summary = "This is a summary."
        summary = self.summarizer.generate_summary(text)

        self.assertEqual(summary, expected_summary)

    def test_get_base_prompt(self):
        text = "This is the text."
        base_prompt = self.summarizer._get_user_message(text)

        self.assertIn(text, base_prompt)

    def test_decide_model_gpt3(self):
        message = "Test message that fits in GPT-3"
        base_prompt = self.summarizer._get_user_message(message)
        prompt, model = self.summarizer._decide_model(base_prompt)

        self.assertEqual(model, "gpt-3.5-turbo")

    def test_decide_model_gpt4(self):
        message = "a " * 5_000
        base_prompt = self.summarizer._get_user_message(message)
        prompt, model = self.summarizer._decide_model(base_prompt)

        self.assertEqual(model, "gpt-4")

    def test_decide_model_reduce_prompt(self):
        message = "a " * 10_000
        base_prompt = self.summarizer._get_user_message(message)
        prompt, model = self.summarizer._decide_model(base_prompt)
        encoded_prompt = self.summarizer._get_tokenizer().encode(prompt)

        self.assertLess(len(encoded_prompt), self.summarizer.GPT_4_LIMIT)


if __name__ == "__main__":
    unittest.main()
