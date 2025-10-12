"""
Phoenix 可观测性工具集成
提供RAG流程的可视化追踪和调试功能
"""

import os
from typing import Optional
from src.logger import setup_logger

logger = setup_logger('phoenix_utils')

# 全局Phoenix会话
_phoenix_session = None


def start_phoenix_ui(port: int = 6006) -> Optional[any]:
    """启动Phoenix可视化界面
    
    Args:
        port: Phoenix UI端口号，默认6006
        
    Returns:
        Phoenix会话对象，如果启动失败则返回None
    """
    global _phoenix_session
    
    # 如果已经启动，直接返回
    if _phoenix_session is not None:
        logger.info(f"Phoenix UI 已在运行: http://localhost:{port}")
        return _phoenix_session
    
    try:
        import phoenix as px
        from phoenix.otel import register
        from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
        
        # 启动Phoenix应用
        _phoenix_session = px.launch_app(port=port)
        
        # 配置OpenTelemetry追踪
        tracer_provider = register()
        LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)
        
        logger.info(f"✅ Phoenix UI 已启动: http://localhost:{port}")
        print(f"\n🔍 Phoenix可观测性平台已启动")
        print(f"   访问地址: http://localhost:{port}")
        print(f"   功能:")
        print(f"   - 📊 实时追踪RAG查询流程")
        print(f"   - 🔍 向量检索可视化")
        print(f"   - 📈 性能分析和统计")
        print(f"   - 🐛 调试和问题诊断\n")
        
        return _phoenix_session
        
    except ImportError as e:
        logger.error(f"Phoenix未安装: {e}")
        print("❌ Phoenix未安装，请运行：pip install arize-phoenix openinference-instrumentation-llama-index")
        return None
    except Exception as e:
        logger.error(f"Phoenix启动失败: {e}")
        print(f"❌ Phoenix启动失败: {e}")
        return None


def stop_phoenix_ui():
    """停止Phoenix UI"""
    global _phoenix_session
    
    if _phoenix_session is not None:
        try:
            # Phoenix会话通常会在进程结束时自动清理
            logger.info("Phoenix UI 会话已关闭")
            print("✅ Phoenix UI 已停止")
            _phoenix_session = None
        except Exception as e:
            logger.error(f"停止Phoenix失败: {e}")


def is_phoenix_running() -> bool:
    """检查Phoenix是否正在运行
    
    Returns:
        True if running, False otherwise
    """
    return _phoenix_session is not None


def get_phoenix_url(port: int = 6006) -> str:
    """获取Phoenix UI的访问地址
    
    Args:
        port: Phoenix UI端口号
        
    Returns:
        Phoenix UI的完整URL
    """
    return f"http://localhost:{port}"


if __name__ == "__main__":
    # 测试启动Phoenix
    print("=== 测试Phoenix启动 ===")
    session = start_phoenix_ui()
    
    if session:
        print(f"\n✅ Phoenix测试成功！")
        print(f"   访问: {get_phoenix_url()}")
        print(f"   按Ctrl+C退出")
        
        try:
            # 保持运行
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n停止Phoenix...")
            stop_phoenix_ui()
    else:
        print("\n❌ Phoenix测试失败")

