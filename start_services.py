"""
服务启动脚本：同时启动 FastAPI 和 Streamlit 服务

主要功能：
- start_fastapi()：启动 FastAPI 服务（端口 8000）
- start_streamlit()：启动 Streamlit 服务（端口 8501）
- monitor_processes()：监控进程输出并添加前缀标识
- handle_signal()：处理信号中断，优雅关闭所有进程
- main()：主函数，协调所有服务启动

执行流程：
1. 检查端口占用
2. 同时启动 FastAPI 和 Streamlit 进程
3. 实时监控并显示日志输出
4. 处理 Ctrl+C 信号，优雅关闭所有服务

特性：
- 跨平台支持（Windows/Linux/Mac）
- 实时日志输出，带服务标识前缀
- 优雅关闭，确保资源清理
- 进程异常退出检测和处理
"""

import os
import sys
import signal
import subprocess
import threading
from pathlib import Path
from typing import Optional, List

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.infrastructure.logger import get_logger

logger = get_logger('start_services')

# 全局进程列表
processes: List[subprocess.Popen[str]] = []
shutdown_flag = threading.Event()


def read_output(process: subprocess.Popen[str], prefix: str, stream_type: str) -> None:
    """读取进程输出并添加前缀标识
    
    Args:
        process: 进程对象
        prefix: 输出前缀（如 [FastAPI]）
        stream_type: 流类型（'stdout' 或 'stderr'）
    """
    stream = process.stdout if stream_type == 'stdout' else process.stderr
    if stream is None:
        return
    
    try:
        # 使用无缓冲模式读取，确保实时输出
        # Windows 上 select 不支持文件描述符，使用简单循环
        if sys.platform == "win32":
            while not shutdown_flag.is_set():
                line = stream.readline()
                if not line:  # EOF 或进程结束
                    # 检查进程是否还在运行
                    if process.poll() is not None:
                        break
                    # 短暂休眠避免 CPU 占用过高
                    import time
                    time.sleep(0.1)
                    continue
                # 去除末尾换行符，添加前缀
                line = line.rstrip('\n\r')
                if line:
                    print(f"{prefix} {line}", flush=True)
        else:
            # Unix 系统可以使用 select
            import select
            while not shutdown_flag.is_set():
                # 检查是否有数据可读
                if stream.fileno() >= 0:
                    ready, _, _ = select.select([stream], [], [], 0.1)
                    if not ready:
                        if process.poll() is not None:
                            break
                        continue
                
                line = stream.readline()
                if not line:
                    if process.poll() is not None:
                        break
                    continue
                
                line = line.rstrip('\n\r')
                if line:
                    print(f"{prefix} {line}", flush=True)
    except (ValueError, OSError, BrokenPipeError, AttributeError):
        # 进程已关闭，流已关闭，或 select 不可用
        pass
    finally:
        if stream:
            try:
                stream.close()
            except Exception:
                pass


def start_fastapi(port: int = 8000) -> subprocess.Popen[str]:
    """启动 FastAPI 服务
    
    Args:
        port: FastAPI 服务端口，默认 8000
        
    Returns:
        FastAPI 进程对象
    """
    cmd = [
        sys.executable, "-m", "uvicorn",
        "src.business.rag_api.fastapi_app:app",
        "--host", "127.0.0.1",
        "--port", str(port),
    ]
    
    logger.info("启动 FastAPI 服务", port=port, cmd=" ".join(cmd))
    
    # Windows 上需要特殊处理输出缓冲
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'  # 禁用 Python 缓冲
    # 确保日志输出到 stdout（structlog 默认输出到 stdout）
    env.setdefault('PYTHONIOENCODING', 'utf-8')
    # 确保日志级别设置正确
    env.setdefault('LOG_LEVEL', 'DEBUG')  # 临时设置，确保显示更多日志
    
    # 直接输出到控制台，不通过管道捕获（保持和之前直接运行一样的行为）
    process = subprocess.Popen(
        cmd,
        stdout=None,  # 直接输出到父进程的 stdout
        stderr=None,  # 直接输出到父进程的 stderr
        text=True,
        env=env,
    )
    
    return process


def start_streamlit(port: int = 8501) -> subprocess.Popen[str]:
    """启动 Streamlit 服务
    
    Args:
        port: Streamlit 服务端口，默认 8501
        
    Returns:
        Streamlit 进程对象
    """
    cmd = [
        sys.executable, "-m", "streamlit",
        "run", "app.py",
        "--server.port", str(port),
        "--server.address", "127.0.0.1",
    ]
    
    logger.info("启动 Streamlit 服务", port=port, cmd=" ".join(cmd))
    
    # Windows 上需要特殊处理输出缓冲
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'  # 禁用 Python 缓冲
    # 确保日志输出到 stdout（structlog 默认输出到 stdout）
    env.setdefault('PYTHONIOENCODING', 'utf-8')
    # 确保日志级别设置正确
    env.setdefault('LOG_LEVEL', 'DEBUG')  # 临时设置，确保显示更多日志
    
    # 直接输出到控制台，不通过管道捕获（保持和之前直接运行一样的行为）
    process = subprocess.Popen(
        cmd,
        stdout=None,  # 直接输出到父进程的 stdout
        stderr=None,  # 直接输出到父进程的 stderr
        text=True,
        env=env,
    )
    
    return process


def handle_signal(signum: int, frame) -> None:
    """处理信号中断（Ctrl+C）
    
    Args:
        signum: 信号编号
        frame: 当前堆栈帧
    """
    logger.info("收到中断信号，正在关闭所有服务...")
    shutdown_flag.set()
    shutdown_all_processes()


def shutdown_all_processes() -> None:
    """关闭所有启动的进程"""
    for process in processes:
        if process.poll() is None:  # 进程仍在运行
            try:
                logger.info("终止进程", pid=process.pid)
                process.terminate()
                # 等待进程结束，最多等待 5 秒
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("进程未在 5 秒内结束，强制终止", pid=process.pid)
                    process.kill()
                    process.wait()
            except Exception as e:
                logger.error("关闭进程失败", pid=process.pid, error=str(e))


def monitor_processes() -> None:
    """监控所有进程，等待它们结束"""
    # 等待所有进程结束
    for process in processes:
        try:
            return_code = process.wait()
            if return_code != 0:
                logger.warning("进程异常退出", pid=process.pid, return_code=return_code)
        except Exception as e:
            logger.error("等待进程结束失败", pid=process.pid, error=str(e))


def main() -> None:
    """主函数：启动所有服务"""
    global processes
    
    # 注册信号处理器
    if sys.platform != "win32":
        # Unix 系统支持 signal.SIGINT
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
    else:
        # Windows 系统需要特殊处理
        signal.signal(signal.SIGINT, handle_signal)
        # Windows 不支持 SIGTERM，使用 SIGBREAK 或其他方式
    
    print("=" * 60)
    print("🚀 正在启动服务...")
    print("=" * 60)
    print("")
    print("📍 FastAPI 文档: http://localhost:8000/docs")
    print("📍 Streamlit 界面: http://localhost:8501")
    print("")
    print("💡 按 Ctrl+C 停止所有服务")
    print("=" * 60)
    print("")
    
    try:
        # 启动 FastAPI
        fastapi_process = start_fastapi(port=8000)
        processes.append(fastapi_process)
        
        # 启动 Streamlit
        streamlit_process = start_streamlit(port=8501)
        processes.append(streamlit_process)
        
        # 等待一下，确保进程启动
        import time
        time.sleep(2)
        
        # 检查进程是否还在运行
        if fastapi_process.poll() is not None:
            logger.error("FastAPI 进程启动失败", return_code=fastapi_process.returncode)
        if streamlit_process.poll() is not None:
            logger.error("Streamlit 进程启动失败", return_code=streamlit_process.returncode)
        
        # 监控进程状态（直接等待，日志会直接输出到控制台）
        monitor_processes()
        
    except KeyboardInterrupt:
        logger.info("收到键盘中断")
        handle_signal(signal.SIGINT, None)
    except Exception as e:
        logger.error("启动服务失败", error=str(e), exc_info=True)
        shutdown_all_processes()
        sys.exit(1)
    finally:
        shutdown_all_processes()
        print("")
        print("=" * 60)
        print("✅ 所有服务已关闭")
        print("=" * 60)


if __name__ == "__main__":
    main()