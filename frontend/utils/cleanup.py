"""
资源清理工具模块
"""

import streamlit as st
import logging

log = logging.getLogger('app')


def cleanup_resources():
    """清理应用资源，关闭 Chroma 客户端和后台线程
    
    这个函数会在应用退出时被调用，确保 Chroma 的后台线程被正确终止
    """
    try:
        log.info("🔧 开始清理应用资源...")
        
        # 清理 IndexManager（关闭 Chroma 客户端）
        # 注意：在 Streamlit 中，session_state 可能不可用，所以需要 try-except
        try:
            if hasattr(st, 'session_state') and 'index_manager' in st.session_state:
                index_manager = st.session_state.get('index_manager')
                if index_manager:
                    try:
                        index_manager.close()
                        log.info("✅ 索引管理器已清理")
                    except Exception as e:
                        log.warning(f"⚠️  清理索引管理器时出错: {e}")
        except Exception as e:
            # Streamlit session_state 可能在某些情况下不可用
            log.debug(f"无法访问 session_state: {e}")
        
        # 尝试清理全局资源
        try:
            # 清理全局的 Embedding 模型（如果需要）
            from backend.infrastructure.indexer import clear_embedding_model_cache
            clear_embedding_model_cache()
            log.debug("✅ 全局模型缓存已清理")
        except Exception as e:
            log.debug(f"清理全局模型缓存时出错: {e}")
        
        # 清理 Hugging Face Embedding 资源（线程池和正在进行的请求）
        try:
            from backend.infrastructure.embeddings.hf_inference_embedding import cleanup_hf_embedding_resources
            cleanup_hf_embedding_resources()
            log.debug("✅ Hugging Face Embedding 资源已清理")
        except Exception as e:
            log.debug(f"清理 Hugging Face Embedding 资源时出错: {e}")
        
        log.info("✅ 应用资源清理完成")
    except Exception as e:
        # 使用 print 作为最后的备选方案
        print(f"❌ 清理资源时发生错误: {e}")

