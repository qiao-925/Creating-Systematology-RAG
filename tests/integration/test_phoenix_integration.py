"""
测试Phoenix集成是否正常工作
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

def test_phoenix_import():
    """测试Phoenix导入"""
    print("=== 测试1: Phoenix导入 ===")
    try:
        import phoenix as px
        from phoenix.otel import register
        from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
        print("✅ Phoenix导入成功")
        return True
    except ImportError as e:
        print(f"❌ Phoenix导入失败: {e}")
        return False


def test_phoenix_utils():
    """测试Phoenix工具模块"""
    print("\n=== 测试2: Phoenix工具模块 ===")
    try:
        from src.phoenix_utils import start_phoenix_ui, stop_phoenix_ui, is_phoenix_running
        print("✅ Phoenix工具模块导入成功")
        return True
    except Exception as e:
        print(f"❌ Phoenix工具模块导入失败: {e}")
        return False


def test_llama_debug_handler():
    """测试LlamaDebugHandler导入"""
    print("\n=== 测试3: LlamaDebugHandler ===")
    try:
        from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler
        print("✅ LlamaDebugHandler导入成功")
        return True
    except Exception as e:
        print(f"❌ LlamaDebugHandler导入失败: {e}")
        return False


def test_query_engine_debug_support():
    """测试QueryEngine调试支持"""
    print("\n=== 测试4: QueryEngine调试支持 ===")
    try:
        from src.query_engine import QueryEngine
        import inspect
        
        # 检查__init__是否有enable_debug参数
        sig = inspect.signature(QueryEngine.__init__)
        params = sig.parameters
        
        if 'enable_debug' in params:
            print("✅ QueryEngine支持enable_debug参数")
            return True
        else:
            print("❌ QueryEngine缺少enable_debug参数")
            return False
    except Exception as e:
        print(f"❌ QueryEngine检查失败: {e}")
        return False


def test_chat_manager_debug_support():
    """测试ChatManager调试支持"""
    print("\n=== 测试5: ChatManager调试支持 ===")
    try:
        from src.chat_manager import ChatManager
        import inspect
        
        # 检查__init__是否有enable_debug参数
        sig = inspect.signature(ChatManager.__init__)
        params = sig.parameters
        
        if 'enable_debug' in params:
            print("✅ ChatManager支持enable_debug参数")
            return True
        else:
            print("❌ ChatManager缺少enable_debug参数")
            return False
    except Exception as e:
        print(f"❌ ChatManager检查失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Phoenix集成测试")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    results.append(("Phoenix导入", test_phoenix_import()))
    results.append(("Phoenix工具模块", test_phoenix_utils()))
    results.append(("LlamaDebugHandler", test_llama_debug_handler()))
    results.append(("QueryEngine调试支持", test_query_engine_debug_support()))
    results.append(("ChatManager调试支持", test_chat_manager_debug_support()))
    
    # 统计结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"总计: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 所有测试通过！Phoenix集成成功。")
        print("\n下一步：")
        print("1. 运行 streamlit run app.py 启动应用")
        print("2. 在侧边栏中点击 '🔍 调试模式'")
        print("3. 启动Phoenix UI并测试")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查安装和配置。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

