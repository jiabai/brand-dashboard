import unittest
from datetime import timedelta
from types import SimpleNamespace

from api.v1.utils.llm_operator import LLMOperator


class TestLLMOperator(unittest.TestCase):
    def test_get_config_info_uses_existing_config_fields(self):
        operator = object.__new__(LLMOperator)
        operator.config = SimpleNamespace(
            provider="openai",
            model="gpt-test",
            base_url="https://example.test/v1",
            temperature=0.1,
            top_p=1.0,
            max_tokens=2000,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            timeout=30000,
            max_retries=3,
            use_cache=True,
            stream=False,
        )
        operator._cache_timeout = timedelta(hours=1)

        config_info = operator.get_config_info()

        self.assertTrue(config_info["enable_cache"])
        self.assertFalse(config_info["enable_streaming"])

