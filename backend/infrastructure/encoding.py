"""
编码初始化模块：确保所有输出使用UTF-8编码，支持emoji正确显示

主要功能：
- setup_utf8_encoding()：设置UTF-8编码环境
- ensure_utf8_stdout()：确保标准输出使用UTF-8编码

执行流程：
1. 设置环境变量PYTHONIOENCODING
2. 配置标准输出编码
3. Windows平台设置控制台代码页
4. 返回设置结果

特性：
- UTF-8编码支持
- Windows控制台兼容
- Emoji正确显示
- 自动初始化
- ⚠️ 注意：此模块必须在其他src模块之前导入
"""

import os
import sys
import io
from typing import Optional

# 全局标志，避免重复设置
_encoding_setup_done = False


def setup_utf8_encoding(force: bool = False) -> bool:
    """设置 UTF-8 编码环境
    
    在所有模块加载前调用此函数，确保：
    1. Python 标准输出/错误使用 UTF-8
    2. Windows 控制台代码页设置为 UTF-8
    3. 环境变量 PYTHONIOENCODING 设置为 utf-8
    
    Args:
        force: 是否强制重新设置（即使已经设置过）
        
    Returns:
        是否成功设置编码
    """
    global _encoding_setup_done
    
    # 避免重复设置（除非强制）
    if _encoding_setup_done and not force:
        return True
    
    try:
        # 1. 设置环境变量（最优先，影响所有子进程）
        os.environ["PYTHONIOENCODING"] = "utf-8"
        
        # 2. 设置标准输出编码
        if force or (hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8'):
            try:
                # Python 3.7+ 支持 reconfigure
                if hasattr(sys.stdout, 'reconfigure'):
                    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                else:
                    # 旧版本 Python，使用 TextIOWrapper
                    sys.stdout = io.TextIOWrapper(
                        sys.stdout.buffer,
                        encoding='utf-8',
                        errors='replace',
                        line_buffering=True
                    )
            except (AttributeError, ValueError, OSError) as e:
                # 某些环境下可能不支持，忽略错误
                pass
        
        # 3. 设置标准错误编码
        if force or (hasattr(sys.stderr, 'encoding') and sys.stderr.encoding != 'utf-8'):
            try:
                if hasattr(sys.stderr, 'reconfigure'):
                    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
                else:
                    sys.stderr = io.TextIOWrapper(
                        sys.stderr.buffer,
                        encoding='utf-8',
                        errors='replace',
                        line_buffering=True
                    )
            except (AttributeError, ValueError, OSError) as e:
                pass
        
        # 4. Windows 平台：设置控制台代码页为 UTF-8 (65001)
        if sys.platform == "win32":
            try:
                # 尝试设置控制台代码页
                import subprocess
                result = subprocess.run(
                    ['chcp', '65001'],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                # 注意：chcp 的输出可能是乱码，但我们只需要它执行成功
            except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
                # chcp 命令可能不可用，或者在某些环境中不支持
                # 尝试使用 PowerShell 命令
                try:
                    subprocess.run(
                        ['powershell', '-Command', '[Console]::OutputEncoding = [System.Text.Encoding]::UTF8'],
                        capture_output=True,
                        timeout=1
                    )
                except Exception:
                    pass
        
        _encoding_setup_done = True
        return True
        
    except Exception as e:
        # 编码设置失败不应该影响程序运行
        # 只记录错误，不抛出异常
        try:
            print(f"Warning: Failed to setup UTF-8 encoding: {e}", file=sys.stderr)
        except Exception:
            pass
        return False


def ensure_utf8_stdout() -> bool:
    """确保 stdout 使用 UTF-8 编码（便捷函数）"""
    return setup_utf8_encoding()


# 模块导入时自动执行一次（除非被禁用）
if os.getenv("DISABLE_AUTO_UTF8_SETUP", "").lower() != "true":
    setup_utf8_encoding()

