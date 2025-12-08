"""
批量执行所有测试
按阶段顺序执行测试，记录失败用例，生成测试报告
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


class TestRunner:
    """测试执行器"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path(__file__).parent / "reports"
        self.output_dir.mkdir(exist_ok=True)
        
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_file = self.output_dir / f"test_report_{self.timestamp}.json"
        self.summary_file = self.output_dir / f"test_summary_{self.timestamp}.txt"
        
        self.results = {
            "timestamp": self.timestamp,
            "stages": [],
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "failed_tests": [],
        }
    
    def run_stage(self, stage_name: str, test_paths: List[str], markers: List[str] = None) -> Dict[str, Any]:
        """执行一个阶段的测试"""
        print(f"\n{'='*60}")
        print(f"执行阶段: {stage_name}")
        print(f"{'='*60}\n")
        
        stage_result = {
            "stage": stage_name,
            "test_paths": test_paths,
            "markers": markers or [],
            "tests_run": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "failed_tests": [],
            "output": "",
        }
        
        # 构建pytest命令
        cmd = ["python", "-m", "pytest"]
        cmd.extend(test_paths)
        
        # 添加markers
        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])
        
        # 添加输出选项
        cmd.extend([
            "-v",  # 详细输出
            "--tb=short",  # 简短traceback
            "--strict-markers",  # 严格标记
        ])
        
        # 执行测试
        try:
            print(f"执行命令: {' '.join(cmd)}\n")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,  # 1小时超时
            )
            
            stage_result["output"] = result.stdout + result.stderr
            stage_result["returncode"] = result.returncode
            
            # 解析输出（简单解析）
            output_lines = result.stdout.split("\n")
            for line in output_lines:
                if "passed" in line.lower() and "failed" in line.lower():
                    # 尝试解析统计信息
                    parts = line.split()
                    for part in parts:
                        if part.isdigit():
                            stage_result["tests_run"] = int(part)
                            break
                elif "FAILED" in line or "ERROR" in line:
                    stage_result["failed_tests"].append(line.strip())
            
            # 根据返回码判断
            if result.returncode == 0:
                print(f"[PASS] {stage_name} 测试通过")
            else:
                print(f"[FAIL] {stage_name} 测试失败 (返回码: {result.returncode})")
                print(f"失败测试: {len(stage_result['failed_tests'])}")
            
            print(f"\n输出摘要:\n{result.stdout[:500]}...")
            
        except subprocess.TimeoutExpired:
            stage_result["error"] = "测试执行超时"
            print(f"[TIMEOUT] {stage_name} 测试超时")
        except Exception as e:
            stage_result["error"] = str(e)
            print(f"[ERROR] {stage_name} 执行出错: {e}")
        
        self.results["stages"].append(stage_result)
        return stage_result
    
    def generate_summary(self):
        """生成测试摘要"""
        summary_lines = [
            "=" * 60,
            "测试执行摘要",
            "=" * 60,
            f"执行时间: {self.timestamp}",
            "",
        ]
        
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        
        for stage in self.results["stages"]:
            summary_lines.append(f"\n阶段: {stage['stage']}")
            summary_lines.append(f"  测试路径: {', '.join(stage['test_paths'])}")
            summary_lines.append(f"  执行测试: {stage.get('tests_run', 0)}")
            summary_lines.append(f"  失败测试: {len(stage.get('failed_tests', []))}")
            
            if stage.get('error'):
                summary_lines.append(f"  错误: {stage['error']}")
            
            total_tests += stage.get('tests_run', 0)
        
        summary_lines.extend([
            "",
            "=" * 60,
            "总计",
            "=" * 60,
            f"总测试数: {total_tests}",
            f"通过: {total_passed}",
            f"失败: {total_failed}",
            f"跳过: {total_skipped}",
            "",
        ])
        
        # 失败的测试
        if self.results["failed_tests"]:
            summary_lines.extend([
                "=" * 60,
                "失败测试列表",
                "=" * 60,
            ])
            for failed_test in self.results["failed_tests"]:
                summary_lines.append(f"  - {failed_test}")
        
        summary_text = "\n".join(summary_lines)
        
        # 写入文件
        with open(self.summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_text)
        
        print("\n" + summary_text)
        return summary_text
    
    def save_results(self):
        """保存测试结果"""
        with open(self.report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n测试结果已保存到: {self.report_file}")
        print(f"测试摘要已保存到: {self.summary_file}")


def main():
    """主函数：按阶段执行所有测试"""
    runner = TestRunner()
    
    # 定义测试阶段
    test_stages = [
        {
            "name": "阶段1: 基础设施层单元测试",
            "paths": [
                "tests/unit/test_embeddings.py",
                "tests/unit/test_data_source.py",
                "tests/unit/test_observers.py",
            ],
        },
        {
            "name": "阶段2: 检索器和路由模块测试",
            "paths": [
                "tests/unit/test_query_router.py",
                "tests/unit/test_grep_retriever.py",
                "tests/unit/test_multi_strategy_retriever.py",
                "tests/unit/test_result_merger.py",
            ],
        },
        {
            "name": "阶段3: 业务层核心模块测试",
            "paths": [
                "tests/test_rag_service.py",
                "tests/test_modular_query_engine.py",
            ],
        },
        {
            "name": "阶段4: 集成测试",
            "paths": [
                "tests/integration/test_rag_service_integration.py",
                "tests/integration/test_multi_strategy_integration.py",
                "tests/integration/test_auto_routing_integration.py",
                "tests/integration/test_reranker_integration.py",
                "tests/integration/test_observability_integration.py",
            ],
        },
        {
            "name": "阶段5: E2E测试",
            "paths": [
                "tests/e2e/test_core_workflows.py",
            ],
        },
        {
            "name": "阶段6: UI测试",
            "paths": [
                "tests/ui/test_app.py",
            ],
        },
        {
            "name": "阶段7: 性能测试",
            "paths": [
                "tests/performance/test_query_performance.py",
                "tests/performance/test_multi_strategy_performance.py",
                "tests/performance/test_reranker_performance.py",
            ],
            "markers": ["performance"],
        },
        {
            "name": "阶段8: 兼容性测试",
            "paths": [
                "tests/compatibility/test_cross_platform.py",
            ],
        },
        {
            "name": "阶段9: 回归测试",
            "paths": [
                "tests/regression/test_core_features.py",
                "tests/regression/test_ui_features.py",
            ],
        },
    ]
    
    # 执行每个阶段
    for stage in test_stages:
        runner.run_stage(
            stage_name=stage["name"],
            test_paths=stage["paths"],
            markers=stage.get("markers"),
        )
    
    # 生成摘要和保存结果
    runner.generate_summary()
    runner.save_results()
    
    # 返回状态码
    failed_stages = [s for s in runner.results["stages"] if s.get("returncode", 0) != 0]
    
    if failed_stages:
        print(f"\n[WARNING] 有 {len(failed_stages)} 个阶段测试失败")
        return 1
    else:
        print("\n[SUCCESS] 所有测试阶段执行完成")
        return 0


if __name__ == "__main__":
    sys.exit(main())

