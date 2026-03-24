"""
LLM 工厂函数单元测试

对齐当前 LiteLLM 工厂实现以及旧 DeepSeek 兼容包装层。
"""

import os
from unittest.mock import Mock, patch

import pytest

from backend.infrastructure.config.models import LLMModelConfig
from backend.infrastructure.llms.factory import (
    create_deepseek_llm,
    create_deepseek_llm_for_query,
    create_deepseek_llm_for_structure,
    create_llm,
)


def _make_model_config(
    *,
    model_id: str = "deepseek-chat",
    litellm_model: str = "deepseek/deepseek-chat",
    api_key_env: str = "DEEPSEEK_API_KEY",
    temperature: float | None = 0.7,
    max_tokens: int | None = 4096,
    supports_reasoning: bool = False,
    request_timeout: float | None = 30.0,
) -> LLMModelConfig:
    return LLMModelConfig(
        id=model_id,
        name=model_id,
        litellm_model=litellm_model,
        api_key_env=api_key_env,
        temperature=temperature,
        max_tokens=max_tokens,
        supports_reasoning=supports_reasoning,
        request_timeout=request_timeout,
    )


def _make_config_mock(
    model_config: LLMModelConfig,
    *,
    default_model_id: str | None = None,
    max_retries: int = 3,
    retry_delay: float = 2.0,
) -> Mock:
    config_mock = Mock()
    config_mock.LLM_MODEL = default_model_id or model_config.id
    config_mock.get_default_llm_id.return_value = default_model_id or model_config.id
    config_mock.get_llm_model_config.side_effect = (
        lambda model_id: model_config if model_id == model_config.id else None
    )
    config_mock.get_available_llm_models.return_value = [model_config]
    config_mock.get_llm_config.return_value = {
        "initialization_timeout": 30.0,
        "max_retries": max_retries,
        "retry_delay": retry_delay,
    }
    return config_mock


class TestCreateLLM:
    """测试当前 LiteLLM 工厂入口。"""

    def test_create_llm_with_default_model(self):
        model_config = _make_model_config()
        config_mock = _make_config_mock(model_config)
        llm_instance = Mock()

        with (
            patch("backend.infrastructure.llms.factory.config", config_mock),
            patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}, clear=True),
            patch("llama_index.llms.litellm.LiteLLM", return_value=llm_instance) as mock_litellm,
        ):
            result = create_llm()

        assert result is llm_instance
        mock_litellm.assert_called_once_with(
            model="deepseek/deepseek-chat",
            api_key="test-key",
            request_timeout=30.0,
            max_tokens=4096,
            temperature=0.7,
        )

    def test_create_llm_omits_temperature_for_reasoning_model(self):
        model_config = _make_model_config(
            model_id="deepseek-reasoner",
            litellm_model="deepseek/deepseek-reasoner",
            temperature=None,
            max_tokens=32768,
            supports_reasoning=True,
            request_timeout=60.0,
        )
        config_mock = _make_config_mock(model_config)

        with (
            patch("backend.infrastructure.llms.factory.config", config_mock),
            patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}, clear=True),
            patch("llama_index.llms.litellm.LiteLLM") as mock_litellm,
            patch("backend.infrastructure.llms.factory.logger") as mock_logger,
        ):
            create_llm(model_id="deepseek-reasoner", temperature=0.1)

        call_kwargs = mock_litellm.call_args.kwargs
        assert "temperature" not in call_kwargs
        assert call_kwargs["model"] == "deepseek/deepseek-reasoner"
        assert call_kwargs["max_tokens"] == 32768
        mock_logger.debug.assert_called()

    def test_create_llm_raises_when_api_key_missing(self):
        model_config = _make_model_config()
        config_mock = _make_config_mock(model_config)

        with (
            patch("backend.infrastructure.llms.factory.config", config_mock),
            patch.dict(os.environ, {}, clear=True),
        ):
            with pytest.raises(ValueError, match="未设置 DEEPSEEK_API_KEY"):
                create_llm()

    def test_create_llm_retries_on_initialization_failure(self):
        model_config = _make_model_config()
        config_mock = _make_config_mock(model_config, max_retries=2, retry_delay=0.0)
        llm_instance = Mock()

        with (
            patch("backend.infrastructure.llms.factory.config", config_mock),
            patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}, clear=True),
            patch(
                "llama_index.llms.litellm.LiteLLM",
                side_effect=[RuntimeError("boom"), llm_instance],
            ) as mock_litellm,
            patch("backend.infrastructure.llms.factory.time.sleep") as mock_sleep,
        ):
            result = create_llm()

        assert result is llm_instance
        assert mock_litellm.call_count == 2
        mock_sleep.assert_called_once_with(0.0)


class TestDeepSeekCompatibilityWrappers:
    """测试向后兼容的 DeepSeek 包装函数。"""

    @patch("backend.infrastructure.llms.factory.create_llm")
    def test_create_deepseek_llm_enables_json_output(self, mock_create_llm):
        mock_instance = Mock()
        mock_create_llm.return_value = mock_instance

        result = create_deepseek_llm(use_json_output=True)

        assert result is mock_instance
        mock_create_llm.assert_called_once_with(
            model_id="deepseek-chat",
            temperature=None,
            max_tokens=None,
            response_format={"type": "json_object"},
        )

    @patch("backend.infrastructure.llms.factory.create_llm")
    def test_create_deepseek_llm_maps_reasoner_model(self, mock_create_llm):
        mock_instance = Mock()
        mock_create_llm.return_value = mock_instance

        result = create_deepseek_llm(model="deepseek-reasoner", max_tokens=1024)

        assert result is mock_instance
        mock_create_llm.assert_called_once_with(
            model_id="deepseek-reasoner",
            temperature=None,
            max_tokens=1024,
        )

    @patch("backend.infrastructure.llms.factory.create_llm")
    def test_create_deepseek_llm_falls_back_to_chat_for_unknown_model(self, mock_create_llm):
        create_deepseek_llm(model="custom-model")

        mock_create_llm.assert_called_once_with(
            model_id="deepseek-chat",
            temperature=None,
            max_tokens=None,
        )

    @pytest.mark.parametrize(
        ("factory_fn", "expected_json_output"),
        [
            (create_deepseek_llm_for_query, False),
            (create_deepseek_llm_for_structure, True),
        ],
    )
    @patch("backend.infrastructure.llms.factory.create_deepseek_llm")
    def test_query_and_structure_wrappers_delegate(
        self,
        mock_create_deepseek_llm,
        factory_fn,
        expected_json_output,
    ):
        mock_instance = Mock()
        mock_create_deepseek_llm.return_value = mock_instance

        result = factory_fn(max_tokens=2048)

        assert result is mock_instance
        mock_create_deepseek_llm.assert_called_once_with(
            api_key=None,
            model=None,
            max_tokens=2048,
            use_json_output=expected_json_output,
        )
