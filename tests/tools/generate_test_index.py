"""
生成测试元数据索引

自动扫描测试文件，提取元数据信息，生成 test_index.json 索引文件。
"""

import ast
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime
import re


class TestIndexGenerator:
    """测试索引生成器"""
    
    def __init__(self, tests_dir: Path, output_file: Path):
        self.tests_dir = tests_dir
        self.output_file = output_file
        self.test_files: List[Dict] = []
        
    def scan_test_files(self) -> List[Path]:
        """扫描所有测试文件"""
        test_files = []
        
        for pattern in ["test_*.py", "*_test.py"]:
            test_files.extend(self.tests_dir.rglob(pattern))
        
        # 排除 __pycache__ 和虚拟环境
        test_files = [
            f for f in test_files
            if "__pycache__" not in str(f) and "venv" not in str(f)
        ]
        
        return sorted(set(test_files))
    
    def parse_test_file(self, file_path: Path) -> Optional[Dict]:
        """解析测试文件，提取元数据"""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
        except Exception as e:
            print(f"警告: 无法解析 {file_path}: {e}", file=sys.stderr)
            return None
        
        metadata = {
            "file_path": str(file_path.relative_to(self.tests_dir.parent)),
            "category": self._infer_category(file_path),
            "test_count": 0,
            "description": "",
            "target_module": "",
            "target_class": "",
            "target_functions": [],
            "coverage": [],
            "dependencies": [],
            "tags": [],
            "pytest_markers": [],
            "fixtures_used": [],
            "related_tests": [],
            "source_files": []
        }
        
        # 提取模块级信息
        self._extract_module_info(tree, metadata)
        
        # 提取测试类和函数
        self._extract_test_classes_and_functions(tree, metadata)
        
        # 提取导入信息，推断目标模块
        self._extract_imports(tree, metadata)
        
        # 提取 fixtures
        self._extract_fixtures(tree, metadata)
        
        # 提取 pytest 标记
        self._extract_pytest_markers(tree, metadata)
        
        # 推断源文件
        self._infer_source_files(file_path, metadata)
        
        # 提取描述
        self._extract_description(tree, metadata)
        
        # 推断标签
        self._infer_tags(metadata)
        
        return metadata
    
    def _infer_category(self, file_path: Path) -> str:
        """推断测试分类"""
        path_str = str(file_path)
        
        if "/unit/" in path_str or "\\unit\\" in path_str:
            return "unit"
        elif "/integration/" in path_str or "\\integration\\" in path_str:
            return "integration"
        elif "/e2e/" in path_str or "\\e2e\\" in path_str:
            return "e2e"
        elif "/performance/" in path_str or "\\performance\\" in path_str:
            return "performance"
        elif "/compatibility/" in path_str or "\\compatibility\\" in path_str:
            return "compatibility"
        elif "/regression/" in path_str or "\\regression\\" in path_str:
            return "regression"
        elif "/ui/" in path_str or "\\ui\\" in path_str:
            return "ui"
        else:
            return "unknown"
    
    def _extract_module_info(self, tree: ast.AST, metadata: Dict):
        """提取模块级信息"""
        # 查找模块级 docstring (兼容 Python 3.8+)
        if tree.body and isinstance(tree.body[0], ast.Expr):
            value = tree.body[0].value
            if isinstance(value, ast.Str):
                # Python 3.7 及以下
                metadata["description"] = value.s
            elif isinstance(value, ast.Constant) and isinstance(value.value, str):
                # Python 3.8+
                metadata["description"] = value.value
        
        # 查找元数据注释
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr):
                value = node.value
                content = None
                if isinstance(value, ast.Str):
                    content = value.s
                elif isinstance(value, ast.Constant) and isinstance(value.value, str):
                    content = value.value
                
                if content and ("测试索引元数据:" in content or "test metadata:" in content.lower()):
                    self._parse_metadata_comment(content, metadata)
    
    def _parse_metadata_comment(self, content: str, metadata: Dict):
        """解析元数据注释"""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('- '):
                if 'category:' in line:
                    metadata["category"] = line.split(':', 1)[1].strip()
                elif 'target_module:' in line:
                    metadata["target_module"] = line.split(':', 1)[1].strip()
                elif 'target_class:' in line:
                    metadata["target_class"] = line.split(':', 1)[1].strip()
                elif 'tags:' in line:
                    # 解析列表格式 [tag1, tag2]
                    match = re.search(r'\[(.*?)\]', line)
                    if match:
                        metadata["tags"] = [t.strip() for t in match.group(1).split(',')]
    
    def _extract_test_classes_and_functions(self, tree: ast.AST, metadata: Dict):
        """提取测试类和函数"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 检查是否是测试类
                if node.name.startswith('Test'):
                    metadata["test_count"] += len([
                        n for n in node.body
                        if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')
                    ])
                    
                    # 从类名推断目标类
                    if not metadata["target_class"]:
                        class_name = node.name[4:]  # 去掉 "Test" 前缀
                        metadata["target_class"] = class_name
            
            elif isinstance(node, ast.FunctionDef):
                if node.name.startswith('test_'):
                    metadata["test_count"] += 1
    
    def _extract_imports(self, tree: ast.AST, metadata: Dict):
        """提取导入信息，推断目标模块"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith('src.'):
                    # 推断目标模块
                    if not metadata["target_module"]:
                        metadata["target_module"] = node.module
                    
                    # 提取导入的类名
                    for alias in node.names:
                        if isinstance(alias, ast.alias):
                            if not metadata["target_class"] and alias.name:
                                # 如果类名以 Test 开头，去掉前缀
                                if alias.name.startswith('Test'):
                                    metadata["target_class"] = alias.name[4:]
                                elif not any(c.islower() for c in alias.name):
                                    # 可能是类名（全大写或首字母大写）
                                    metadata["target_class"] = alias.name
            
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name and alias.name.startswith('src.'):
                        if not metadata["target_module"]:
                            metadata["target_module"] = alias.name
    
    def _extract_fixtures(self, tree: ast.AST, metadata: Dict):
        """提取使用的 fixtures"""
        fixtures = set()
        
        for node in ast.walk(tree):
            # 查找函数参数中的 fixtures
            if isinstance(node, ast.FunctionDef):
                for arg in node.args.args:
                    if arg.arg not in ['self', 'cls']:
                        fixtures.add(arg.arg)
            
            # 查找 @pytest.fixture 装饰器
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Attribute):
                        if decorator.attr == 'fixture':
                            fixtures.add(node.name)
        
        metadata["fixtures_used"] = sorted(list(fixtures))
    
    def _extract_pytest_markers(self, tree: ast.AST, metadata: Dict):
        """提取 pytest 标记"""
        markers = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Attribute):
                            if decorator.func.attr == 'mark':
                                # 提取标记名
                                if decorator.args:
                                    if isinstance(decorator.args[0], ast.Name):
                                        markers.add(decorator.args[0].id)
                                    elif isinstance(decorator.args[0], ast.Str):
                                        markers.add(decorator.args[0].s)
        
        metadata["pytest_markers"] = sorted(list(markers))
    
    def _infer_source_files(self, file_path: Path, metadata: Dict):
        """推断对应的源文件"""
        source_files = []
        
        # 从文件名推断
        file_name = file_path.stem  # test_indexer
        if file_name.startswith('test_'):
            module_name = file_name[5:]  # indexer
            # 尝试多个可能的路径
            possible_paths = [
                f"src/{module_name}.py",
                f"src/{module_name.replace('_', '/')}.py",
            ]
            
            for path_str in possible_paths:
                source_path = self.tests_dir.parent / path_str
                if source_path.exists():
                    source_files.append(path_str)
                    break
        
        # 从 target_module 推断
        if metadata["target_module"]:
            module_path = metadata["target_module"].replace('.', '/') + '.py'
            source_path = self.tests_dir.parent / module_path
            if source_path.exists():
                source_file = module_path
                if source_file not in source_files:
                    source_files.append(source_file)
        
        metadata["source_files"] = sorted(source_files)
    
    def _extract_description(self, tree: ast.AST, metadata: Dict):
        """提取描述信息"""
        # 如果没有描述，尝试从模块 docstring 生成
        if not metadata["description"]:
            # 从文件名生成简单描述
            file_path = Path(metadata["file_path"])
            file_name = file_path.stem.replace('test_', '').replace('_', ' ')
            metadata["description"] = f"测试 {file_name} 模块的功能"
    
    def _infer_tags(self, metadata: Dict):
        """推断标签"""
        tags = set(metadata.get("tags", []))
        
        # 添加分类标签
        tags.add(metadata["category"])
        
        # 从文件名推断标签
        file_path = Path(metadata["file_path"])
        file_name = file_path.stem.lower()
        
        if 'integration' in file_name:
            tags.add('integration')
        if 'e2e' in file_name or 'end_to_end' in file_name:
            tags.add('e2e')
        if 'performance' in file_name:
            tags.add('performance')
        if 'github' in file_name:
            tags.add('github')
        if 'phoenix' in file_name:
            tags.add('phoenix')
        
        # 从目标模块推断标签
        if metadata["target_module"]:
            module_parts = metadata["target_module"].split('.')
            if len(module_parts) > 1:
                tags.add(module_parts[-1])  # 模块名作为标签
        
        metadata["tags"] = sorted(list(tags))
    
    def generate_statistics(self) -> Dict:
        """生成统计信息"""
        by_category = {}
        total_test_cases = 0
        
        for test_file in self.test_files:
            category = test_file.get("category", "unknown")
            by_category[category] = by_category.get(category, 0) + 1
            total_test_cases += test_file.get("test_count", 0)
        
        return {
            "total_test_files": len(self.test_files),
            "by_category": by_category,
            "total_test_cases": total_test_cases,
            "coverage_target": 90.0
        }
    
    def generate(self):
        """生成测试索引"""
        print("扫描测试文件...")
        test_files = self.scan_test_files()
        print(f"找到 {len(test_files)} 个测试文件")
        
        print("\n解析测试文件...")
        for i, test_file in enumerate(test_files, 1):
            print(f"  [{i}/{len(test_files)}] {test_file.name}")
            metadata = self.parse_test_file(test_file)
            if metadata:
                self.test_files.append(metadata)
        
        # 生成索引结构
        index = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "test_files": self.test_files,
            "statistics": self.generate_statistics()
        }
        
        # 保存到文件
        print(f"\n保存索引到 {self.output_file}...")
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        
        print(f"\n索引生成完成:")
        print(f"  - 测试文件数: {index['statistics']['total_test_files']}")
        print(f"  - 测试用例数: {index['statistics']['total_test_cases']}")
        print(f"  - 输出文件: {self.output_file}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="生成测试元数据索引")
    parser.add_argument(
        "-t", "--tests-dir",
        type=Path,
        default=Path(__file__).parent.parent,
        help="测试目录路径（默认: tests/）"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path(__file__).parent.parent / "test_index.json",
        help="输出文件路径（默认: tests/test_index.json）"
    )
    
    args = parser.parse_args()
    
    generator = TestIndexGenerator(args.tests_dir, args.output)
    generator.generate()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

