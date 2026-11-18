#!/usr/bin/env python3
"""
启动时间诊断脚本：测量应用启动各阶段耗时

使用方法：
    python tests/tools/analyze_startup_time.py
    python tests/tools/analyze_startup_time.py --detailed  # 详细模式
    python tests/tools/analyze_startup_time.py --init      # 包含初始化测试

输出示例：
    📊 启动时间诊断报告
    ══════════════════════════════════════════════════════════
    阶段                          耗时(s)    占比      状态
    ──────────────────────────────────────────────────────────
    1. 基础导入                     0.12     8%       ✅
    2. dotenv 加载                  0.03     2%       ✅
    3. 配置模块导入                 0.45    30%       ⚠️ 瓶颈
    4. 初始化模块导入               0.18    12%       ✅
    5. 前端模块导入                 0.22    15%       ✅
    ──────────────────────────────────────────────────────────
    总计（导入阶段）                1.00   100%
"""

import sys
import time
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class TimingResult:
    """计时结果"""
    name: str
    duration: float
    success: bool
    error: Optional[str] = None


class StartupTimingAnalyzer:
    """启动时间分析器"""
    
    def __init__(self, detailed: bool = False):
        self.detailed = detailed
        self.results: list[TimingResult] = []
        self.total_start = time.perf_counter()
    
    def measure(self, name: str):
        """计时上下文管理器"""
        return _TimingContext(self, name)
    
    def add_result(self, result: TimingResult) -> None:
        """添加计时结果"""
        self.results.append(result)
    
    def print_report(self) -> None:
        """打印诊断报告"""
        total_time = sum(r.duration for r in self.results)
        
        print("\n" + "═" * 60)
        print("📊 启动时间诊断报告")
        print("═" * 60)
        print(f"{'阶段':<30} {'耗时(s)':<10} {'占比':<8} {'状态':<6}")
        print("─" * 60)
        
        for i, result in enumerate(self.results, 1):
            pct = (result.duration / total_time * 100) if total_time > 0 else 0
            status = self._get_status(result, pct)
            print(f"{i}. {result.name:<27} {result.duration:>6.2f}    {pct:>5.1f}%    {status}")
            
            if result.error and self.detailed:
                print(f"   └─ 错误: {result.error[:50]}...")
        
        print("─" * 60)
        print(f"{'总计':<30} {total_time:>6.2f}    100.0%")
        print("═" * 60)
        
        # 打印建议
        self._print_suggestions(total_time)
    
    def _get_status(self, result: TimingResult, pct: float) -> str:
        """获取状态标记"""
        if not result.success:
            return "❌"
        if pct > 30:
            return "⚠️ 瓶颈"
        if pct > 20:
            return "🟡"
        return "✅"
    
    def _print_suggestions(self, total_time: float) -> None:
        """打印优化建议"""
        print("\n💡 优化建议:")
        
        # 找出耗时最长的阶段
        if self.results:
            slowest = max(self.results, key=lambda r: r.duration)
            pct = slowest.duration / total_time * 100 if total_time > 0 else 0
            
            if pct > 30:
                print(f"   - 「{slowest.name}」占总耗时 {pct:.1f}%，建议优先优化")
        
        # 总体评估
        if total_time < 1:
            print("   - ✅ 启动时间 < 1秒，性能良好")
        elif total_time < 3:
            print("   - 🟡 启动时间 1-3秒，可接受但有优化空间")
        else:
            print("   - ⚠️ 启动时间 > 3秒，建议实施延迟加载优化")
        
        # 失败的阶段
        failed = [r for r in self.results if not r.success]
        if failed:
            print(f"   - ❌ 有 {len(failed)} 个阶段失败，需要排查")


class _TimingContext:
    """计时上下文管理器"""
    
    def __init__(self, analyzer: StartupTimingAnalyzer, name: str):
        self.analyzer = analyzer
        self.name = name
        self.start: float = 0
    
    def __enter__(self):
        self.start = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start
        success = exc_type is None
        error = str(exc_val) if exc_val else None
        
        self.analyzer.add_result(TimingResult(
            name=self.name,
            duration=duration,
            success=success,
            error=error
        ))
        
        # 不抑制异常，让调用者决定
        return False


def analyze_import_time(detailed: bool = False) -> StartupTimingAnalyzer:
    """分析导入阶段耗时"""
    analyzer = StartupTimingAnalyzer(detailed=detailed)
    
    print("🔍 开始分析启动时间...\n")
    
    # 1. 基础导入
    with analyzer.measure("基础导入 (sys, pathlib)"):
        import sys  # noqa: F401
        from pathlib import Path  # noqa: F401
    
    # 2. dotenv 加载
    with analyzer.measure("dotenv 加载"):
        from dotenv import load_dotenv
        load_dotenv()
    
    # 3. 配置模块导入
    with analyzer.measure("配置模块导入"):
        from backend.infrastructure.config import config  # noqa: F401
    
    # 4. 日志模块导入
    with analyzer.measure("日志模块导入"):
        from backend.infrastructure.logger import get_logger  # noqa: F401
    
    # 5. 初始化模块导入
    with analyzer.measure("初始化模块导入"):
        from backend.infrastructure.initialization.bootstrap import initialize_app  # noqa: F401

    return analyzer


def analyze_init_time(detailed: bool = False) -> StartupTimingAnalyzer:
    """分析初始化阶段耗时（包括模块初始化）"""
    analyzer = StartupTimingAnalyzer(detailed=detailed)
    
    print("🔍 开始分析初始化时间...\n")
    
    # 先完成导入
    with analyzer.measure("导入阶段（总计）"):
        from backend.infrastructure.initialization.bootstrap import initialize_app
        from backend.infrastructure.initialization.manager import InitializationManager
        from backend.infrastructure.initialization.registry import register_all_modules
    
    # 创建管理器
    with analyzer.measure("创建初始化管理器"):
        manager = InitializationManager()
    
    # 注册模块
    with analyzer.measure("注册所有模块"):
        register_all_modules(manager)
    
    # 执行初始化
    with analyzer.measure("执行初始化"):
        try:
            manager.execute_all()
        except Exception as e:
            print(f"   ⚠️ 初始化过程中有错误: {e}")
    
    return analyzer


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="启动时间诊断脚本")
    parser.add_argument("--detailed", "-d", action="store_true", help="显示详细信息")
    parser.add_argument("--init", "-i", action="store_true", help="包含初始化测试")
    args = parser.parse_args()
    
    # 分析导入时间
    print("=" * 60)
    print("📦 阶段1: 导入时间分析")
    print("=" * 60)
    import_analyzer = analyze_import_time(detailed=args.detailed)
    import_analyzer.print_report()
    
    # 可选：分析初始化时间
    if args.init:
        print("\n" + "=" * 60)
        print("🚀 阶段2: 初始化时间分析")
        print("=" * 60)
        init_analyzer = analyze_init_time(detailed=args.detailed)
        init_analyzer.print_report()


if __name__ == "__main__":
    main()
