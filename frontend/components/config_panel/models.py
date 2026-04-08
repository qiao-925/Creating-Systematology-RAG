"""
配置数据模型 - AppConfig 和 LLM 预设定义

主要功能：
- AppConfig: 应用运行时配置，作为 session_state 的读写桥梁
- LLM_PRESETS: LLM 预设配置（精确/平衡/创意）
- get_preset_params(): 获取预设参数
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional

import streamlit as st

from backend.infrastructure.config import config


# LLM 预设定义
LLM_PRESETS: Dict[str, Dict[str, Any]] = {
    "precise": {
        "name": "🎯 精确模式",
        "description": "适合代码、技术问答、数据分析",
        "temperature": 0.3,
        "max_tokens": 4096,
    },
    "balanced": {
        "name": "⚖️ 平衡模式",
        "description": "默认模式，适合大多数场景",
        "temperature": 0.7,
        "max_tokens": 4096,
    },
    "creative": {
        "name": "💡 创意模式",
        "description": "适合头脑风暴、创意写作",
        "temperature": 1.3,
        "max_tokens": 8192,
    },
}


def get_preset_params(preset_key: str) -> Dict[str, Any]:
    """获取预设参数
    
    Args:
        preset_key: 预设键名（precise/balanced/creative）
        
    Returns:
        预设参数字典，包含 temperature 和 max_tokens
    """
    preset = LLM_PRESETS.get(preset_key, LLM_PRESETS["balanced"])
    return {
        "temperature": preset["temperature"],
        "max_tokens": preset["max_tokens"],
    }


@dataclass
class AppConfig:
    """应用运行时配置
    
    作为 session_state 的读写桥梁，不在 session_state 中存储实例本身。
    """
    
    # 模型配置
    selected_model: str = "deepseek-chat"
    llm_preset: str = "balanced"
    
    # RAG 配置
    retrieval_strategy: str = "vector"
    use_agentic_rag: bool = False
    similarity_top_k: int = 3
    similarity_threshold: float = 0.4
    enable_rerank: bool = False
    
    # 研究模式
    research_mode: bool = False
    
    # 显示配置
    show_reasoning: bool = True
    
    @classmethod
    def from_session_state(cls) -> "AppConfig":
        """从 session_state 读取配置"""
        return cls(
            selected_model=st.session_state.get(
                'selected_model', config.get_default_llm_id()
            ),
            llm_preset=st.session_state.get('llm_preset', 'balanced'),
            retrieval_strategy=st.session_state.get(
                'retrieval_strategy', config.RETRIEVAL_STRATEGY
            ),
            use_agentic_rag=st.session_state.get('use_agentic_rag', False),
            similarity_top_k=st.session_state.get(
                'similarity_top_k', config.SIMILARITY_TOP_K
            ),
            similarity_threshold=st.session_state.get(
                'similarity_threshold', config.SIMILARITY_THRESHOLD
            ),
            enable_rerank=st.session_state.get(
                'enable_rerank', config.ENABLE_RERANK
            ),
            research_mode=st.session_state.get('research_mode', False),
            show_reasoning=st.session_state.get(
                'show_reasoning', config.DEEPSEEK_ENABLE_REASONING_DISPLAY
            ),
        )
    
    def save_to_session_state(self) -> None:
        """写入 session_state"""
        st.session_state.selected_model = self.selected_model
        st.session_state.llm_preset = self.llm_preset
        st.session_state.retrieval_strategy = self.retrieval_strategy
        st.session_state.use_agentic_rag = self.use_agentic_rag
        st.session_state.similarity_top_k = self.similarity_top_k
        st.session_state.similarity_threshold = self.similarity_threshold
        st.session_state.enable_rerank = self.enable_rerank
        st.session_state.research_mode = self.research_mode
        st.session_state.show_reasoning = self.show_reasoning
    
    def get_llm_temperature(self) -> Optional[float]:
        """获取当前预设的 temperature
        
        Returns:
            temperature 值，推理模型返回 None
        """
        # 检查是否为推理模型
        model_config = config.get_llm_model_config(self.selected_model)
        if model_config and model_config.supports_reasoning:
            return None
        
        preset_params = get_preset_params(self.llm_preset)
        return preset_params["temperature"]
    
    def get_llm_max_tokens(self) -> int:
        """获取当前预设的 max_tokens"""
        preset_params = get_preset_params(self.llm_preset)
        return preset_params["max_tokens"]
