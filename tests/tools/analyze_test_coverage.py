#!/usr/bin/env python3
"""
测试覆盖率分析工具
分析源文件和测试文件的对应关系，找出缺失的测试
"""

import json
import os
import sys
import io
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Windows 编码兼容性
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def get_source_files() -> Set[str]:
    """获取所有源文件"""
    src_dir = project_root / "src"
    source_files = set()
    
    for py_file in src_dir.rglob("*.py"):
        # 跳过 __pycache__ 和 __init__.py (如果是空的兼容层)
        if "__pycache__" in str(py_file):
            continue
        
        # 转换为模块路径 (相对于 src)
        rel_path = py_file.relative_to(src_dir)
        module_path = str(rel_path).replace("\\", "/").replace("/", ".").replace(".py", "")
        
        # 跳过空的兼容层文件（只包含导入的）
        if module_path.endswith("__init__"):
            continue
            
        source_files.add(module_path)
    
    return source_files


def get_test_files() -> Dict[str, List[str]]:
    """获取所有测试文件及其覆盖的源模块"""
    test_index_path = project_root / "tests" / "test_index.json"
    
    if not test_index_path.exists():
        print("⚠️  test_index.json 不存在，请先运行: python tests/tools/generate_test_index.py")
        return {}
    
    with open(test_index_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    test_mapping = defaultdict(list)
    
    for test_file_info in data.get("test_files", []):
        test_path = test_file_info.get("file_path", "")
        source_files = test_file_info.get("source_files", [])
        
        # 提取模块路径
        for src_file in source_files:
            # src/indexer.py -> indexer
            # src/business/rag_service.py -> business.rag_service
            if src_file.startswith("src/"):
                module_path = src_file.replace("src/", "").replace(".py", "").replace("/", ".")
                test_mapping[module_path].append(test_path)
    
    return dict(test_mapping)


def get_category_statistics() -> Dict[str, int]:
    """获取测试分类统计"""
    test_index_path = project_root / "tests" / "test_index.json"
    
    if not test_index_path.exists():
        return {}
    
    with open(test_index_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    categories = defaultdict(int)
    
    for test_file_info in data.get("test_files", []):
        category = test_file_info.get("category", "unknown")
        categories[category] += 1
    
    return dict(categories)


def analyze_missing_tests(source_files: Set[str], test_mapping: Dict[str, List[str]]) -> Tuple[List[str], Dict[str, List[str]]]:
    """分析缺失的测试"""
    missing_modules = []
    partially_tested = {}
    
    for module in sorted(source_files):
        # 跳过一些特殊的模块
        if module in ["__init__", "encoding", "phoenix_utils", "vector_version_utils", "activity_logger"]:
            continue
        
        # 检查是否有测试
        if module not in test_mapping:
            missing_modules.append(module)
        else:
            # 检查测试覆盖率
            tests = test_mapping[module]
            # 可以在这里添加更详细的覆盖率分析
            if len(tests) == 0:
                missing_modules.append(module)
            elif len(tests) == 1:
                # 只有单元测试或只有集成测试，可能需要补充
                partially_tested[module] = tests
    
    return missing_modules, partially_tested


def print_analysis_report():
    """打印分析报告"""
    print("=" * 80)
    print("测试体系覆盖率分析报告")
    print("=" * 80)
    print()
    
    # 1. 获取测试统计
    categories = get_category_statistics()
    if categories:
        print("📊 测试分类统计:")
        for cat, count in sorted(categories.items()):
            print(f"  {cat:20s}: {count:3d} 个文件")
        print()
    
    # 2. 获取源文件和测试文件
    print("🔍 分析源文件和测试文件...")
    source_files = get_source_files()
    test_mapping = get_test_files()
    
    print(f"  源文件总数: {len(source_files)}")
    print(f"  有测试覆盖的模块: {len(test_mapping)}")
    print()
    
    # 3. 分析缺失的测试
    missing_modules, partially_tested = analyze_missing_tests(source_files, test_mapping)
    
    # 4. 输出缺失的测试
    if missing_modules:
        print("❌ 缺少测试的模块 ({} 个):".format(len(missing_modules)))
        print()
        for module in missing_modules[:20]:  # 只显示前20个
            print(f"  - {module}")
        if len(missing_modules) > 20:
            print(f"  ... 还有 {len(missing_modules) - 20} 个模块")
        print()
    else:
        print("✅ 所有模块都有测试覆盖")
        print()
    
    # 5. 部分测试的模块
    if partially_tested:
        print("⚠️  只有部分测试覆盖的模块 ({} 个):".format(len(partially_tested)))
        print()
        for module, tests in list(partially_tested.items())[:10]:
            print(f"  - {module}")
            for test in tests:
                print(f"      {test}")
        if len(partially_tested) > 10:
            print(f"  ... 还有 {len(partially_tested) - 10} 个模块")
        print()
    
    # 6. 关键模块检查
    print("🔑 关键模块测试覆盖检查:")
    print()
    critical_modules = [
        "indexer.index_core",
        "indexer.index_manager",
        "query.modular.engine",
        "query.modular.query_processor",
        "business.services.rag_service",
        "business.strategy_manager",
        "business.registry",
        "retrievers.multi_strategy_retriever",
        "rerankers.base",
        "embeddings.factory",
        "data_loader",
        "data_source.github_source",
    ]
    
    for module in critical_modules:
        if module in test_mapping:
            tests = test_mapping[module]
            print(f"  ✅ {module:40s} ({len(tests)} 个测试)")
        else:
            # 检查是否有部分匹配
            found = False
            for test_module in test_mapping.keys():
                if module in test_module or test_module in module:
                    print(f"  ⚠️  {module:40s} (部分覆盖: {test_module})")
                    found = True
                    break
            if not found:
                print(f"  ❌ {module:40s} (无测试)")
    print()
    
    # 7. 建议
    print("💡 建议:")
    print()
    if missing_modules:
        print("  1. 优先为以下模块补充测试:")
        priority_modules = [m for m in missing_modules if any(keyword in m for keyword in 
            ["core", "manager", "service", "engine", "factory"])]
        for module in priority_modules[:5]:
            print(f"     - {module}")
        print()
    
    print("  2. 检查测试类型分布:")
    print("     - 单元测试应覆盖所有核心业务逻辑")
    print("     - 集成测试应覆盖关键流程")
    print("     - 性能测试应覆盖耗时操作")
    print()
    
    print("  3. 运行覆盖率报告:")
    print("     pytest --cov=src --cov-report=html")
    print()
    
    print("=" * 80)


if __name__ == "__main__":
    print_analysis_report()
