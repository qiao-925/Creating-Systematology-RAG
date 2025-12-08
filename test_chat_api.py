#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
对话 API 接口验证脚本

用于验证新添加的对话会话管理 API 接口是否正常工作
使用方法：
    python test_chat_api.py
    或
    uv run python test_chat_api.py
"""

import json
import sys
import time
from typing import Dict, Any, Optional
import requests
from requests.exceptions import RequestException, ConnectionError

# API 基础地址
BASE_URL = "http://127.0.0.1:8000"


def print_curl_command(method: str, url: str, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> None:
    """打印对应的 curl 命令"""
    curl_parts = ["curl", "-X", method]
    
    # 添加 headers
    if headers:
        for key, value in headers.items():
            curl_parts.append("-H")
            curl_parts.append(f'"{key}: {value}"')
    
    # 添加 Content-Type（如果没有指定）
    if data and not (headers and "Content-Type" in headers):
        curl_parts.append("-H")
        curl_parts.append('"Content-Type: application/json"')
    
    # 添加数据
    if data:
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        # 转义单引号并添加单引号包裹
        json_data_escaped = json_data.replace("'", "'\\''")
        curl_parts.append("-d")
        curl_parts.append(f"'{json_data_escaped}'")
    
    # 添加 URL
    curl_parts.append(url)
    
    curl_command = " ".join(curl_parts)
    print(f"   📋 curl 命令:")
    print(f"   {curl_command}")
    print()

# 测试统计
test_results = {
    "passed": 0,
    "failed": 0,
    "total": 0,
    "errors": []
}


def print_header(title: str) -> None:
    """打印测试标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_test(name: str) -> None:
    """打印测试项"""
    print(f"\n🔍 测试: {name}")


def print_success(message: str = "通过") -> None:
    """打印成功信息"""
    print(f"✅ {message}")
    test_results["passed"] += 1
    test_results["total"] += 1


def print_fail(message: str, error: Optional[str] = None) -> None:
    """打印失败信息"""
    print(f"❌ {message}")
    if error:
        print(f"   错误: {error}")
    test_results["failed"] += 1
    test_results["total"] += 1
    test_results["errors"].append({"test": message, "error": error})


def check_server() -> bool:
    """检查服务器是否运行"""
    try:
        # 尝试访问 API 文档页面来检查服务器是否运行
        url = f"{BASE_URL}/docs"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print_success("服务器运行正常")
            return True
        else:
            print_fail("服务器响应异常", f"状态码: {response.status_code}")
            return False
    except ConnectionError:
        print_fail("无法连接到服务器", f"请确保 FastAPI 服务正在运行 ({BASE_URL})")
        print("   提示: 运行 'make run' 或 'uvicorn src.business.rag_api.fastapi_app:app --host 127.0.0.1 --port 8000'")
        return False
    except Exception as e:
        print_fail("检查服务器时出错", str(e))
        return False


def test_stream_chat_auto_create() -> Optional[str]:
    """测试流式对话（自动创建新会话）"""
    try:
        url = f"{BASE_URL}/chat/stream"
        data = {"message": "你好，这是一条测试消息"}
        print_curl_command("POST", url, data)
        print("   💡 注意: 流式接口需要使用特殊方式接收数据")
        print(f"   curl -X POST '{url}' -H 'Content-Type: application/json' -d '{json.dumps(data, ensure_ascii=False)}' --no-buffer")
        print()
        
        response = requests.post(
            url,
            json=data,
            stream=True,
            timeout=60
        )
        if response.status_code == 200:
            chunks = []
            session_id = None
            
            print("   接收流式数据...")
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        try:
                            chunk = json.loads(data_str)
                            chunk_type = chunk.get("type")
                            
                            if chunk_type == "token":
                                chunks.append(chunk.get("data", ""))
                            elif chunk_type == "sources":
                                print(f"   ✅ 收到来源信息")
                            elif chunk_type == "done":
                                print(f"   ✅ 流式传输完成")
                                # 从 done 事件中获取 session_id
                                done_data = chunk.get("data", {})
                                if isinstance(done_data, dict):
                                    session_id = done_data.get("session_id")
                                    if session_id:
                                        print(f"   📌 会话ID: {session_id}")
                                elif isinstance(done_data, str):
                                    # 兼容旧格式（只有 answer 字符串）
                                    print("   ⚠️  旧格式响应（仅包含答案字符串）")
                            elif chunk_type == "error":
                                error_msg = chunk.get("data", {}).get("message", "未知错误")
                                print_fail("流式对话返回错误", error_msg)
                                return None
                        except json.JSONDecodeError:
                            pass
            
            if chunks:
                answer = "".join(chunks)
                print_success(f"流式对话成功 (接收 {len(chunks)} 个token, 答案长度: {len(answer)})")
                if answer:
                    print(f"   答案预览: {answer[:100]}...")
                
                # 如果流式响应中没有 session_id，需要从历史中获取最新的会话
                if not session_id:
                    # 这里可以通过获取会话列表来找到最新创建的会话
                    # 或者从响应中提取（如果后端返回了）
                    print("   ⚠️  未从流式响应中获取到 session_id，将在后续测试中使用历史接口")
                else:
                    print(f"   📌 会话ID: {session_id}")
                return session_id
            else:
                print_fail("流式对话未接收到数据")
                return None
        else:
            print_fail(f"流式对话失败", f"状态码: {response.status_code}, 响应: {response.text}")
            return None
    except Exception as e:
        print_fail("流式对话时出错", str(e))
        return None


def test_stream_chat_with_session(session_id: str) -> bool:
    """测试流式对话（使用现有会话）"""
    try:
        url = f"{BASE_URL}/chat/stream"
        data = {
            "message": "请介绍一下系统科学的基本概念",
            "session_id": session_id
        }
        print_curl_command("POST", url, data)
        print()
        
        response = requests.post(
            url,
            json=data,
            stream=True,
            timeout=60
        )
        if response.status_code == 200:
            chunks = []
            
            print("   接收流式数据...")
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        try:
                            chunk = json.loads(data_str)
                            chunk_type = chunk.get("type")
                            
                            if chunk_type == "token":
                                chunks.append(chunk.get("data", ""))
                            elif chunk_type == "sources":
                                print(f"   ✅ 收到来源信息")
                            elif chunk_type == "done":
                                print(f"   ✅ 流式传输完成")
                            elif chunk_type == "error":
                                error_msg = chunk.get("data", {}).get("message", "未知错误")
                                print_fail("流式对话返回错误", error_msg)
                                return False
                        except json.JSONDecodeError:
                            pass
            
            if chunks:
                answer = "".join(chunks)
                print_success(f"流式对话成功 (接收 {len(chunks)} 个token, 答案长度: {len(answer)})")
                if answer:
                    print(f"   答案预览: {answer[:100]}...")
                return True
            else:
                print_fail("流式对话未接收到数据")
                return False
        else:
            print_fail(f"流式对话失败", f"状态码: {response.status_code}, 响应: {response.text}")
            return False
    except Exception as e:
        print_fail("流式对话时出错", str(e))
        return False


def test_get_session_history(session_id: str) -> bool:
    """测试获取指定会话历史"""
    print_test("获取指定会话历史")
    try:
        url = f"{BASE_URL}/chat/sessions/{session_id}/history"
        print_curl_command("GET", url)
        
        response = requests.get(
            url,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            history_count = len(data.get("history", []))
            print_success(f"获取会话历史成功 (历史记录数: {history_count})")
            return True
        elif response.status_code == 404:
            print_fail("会话不存在", f"session_id: {session_id}")
            return False
        else:
            print_fail(f"获取会话历史失败", f"状态码: {response.status_code}, 响应: {response.text}")
            return False
    except Exception as e:
        print_fail("获取会话历史时出错", str(e))
        return False


def test_invalid_session() -> bool:
    """测试无效会话ID的处理"""
    print_test("测试无效会话ID处理")
    try:
        url = f"{BASE_URL}/chat/sessions/nonexistent_session_12345/history"
        print_curl_command("GET", url)
        
        response = requests.get(
            url,
            timeout=10
        )
        if response.status_code == 404:
            print_success("正确处理不存在的会话 (返回 404)")
            return True
        else:
            print_fail(f"无效会话处理异常", f"期望 404, 实际: {response.status_code}")
            return False
    except Exception as e:
        print_fail("测试无效会话时出错", str(e))
        return False


def print_summary() -> None:
    """打印测试总结"""
    print_header("测试总结")
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    
    print(f"总测试数: {total}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    
    if failed > 0:
        print("\n失败详情:")
        for i, error in enumerate(test_results["errors"], 1):
            print(f"  {i}. {error['test']}")
            if error['error']:
                print(f"     错误: {error['error']}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！")
        sys.exit(0)
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        sys.exit(1)


def main() -> None:
    """主函数"""
    print_header("对话 API 接口验证测试（极简版）")
    print(f"API 地址: {BASE_URL}")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📝 测试接口:")
    print("  1. POST /chat/stream - 流式对话（自动创建/使用会话）")
    print("  2. GET /chat/sessions/{session_id}/history - 获取会话历史")
    
    # 检查服务器
    if not check_server():
        print("\n⚠️  服务器未运行，无法继续测试")
        sys.exit(1)
    
    # 测试流程
    session_id = None
    
    # 1. 测试流式对话（自动创建会话）
    session_id = test_stream_chat_auto_create()
    
    # 2. 测试流式对话（使用现有会话）
    if session_id:
        test_stream_chat_with_session(session_id)
    
    # 3. 测试获取会话历史
    if session_id:
        test_get_session_history(session_id)
    else:
        # 如果没有获取到 session_id，使用一个测试用的 session_id
        # 实际使用中，应该从流式响应的 done 事件中获取
        print("\n⚠️  未获取到 session_id，跳过会话历史测试")
    
    # 4. 测试错误处理
    test_invalid_session()
    
    # 打印总结
    print_summary()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

