"""
Template Evaluator Module

模板可靠性评估：反事实对比 + 结果导向（Action Advancement）
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from statistics import mean


@dataclass
class CounterfactualResult:
    """反事实评估结果"""
    mean_contribution: float    # 平均贡献度
    min_contribution: float     # 最小贡献度
    test_count: int             # 测试案例数
    passed: bool                # 是否通过


@dataclass
class AdvancementResult:
    """Action Advancement 评估结果"""
    advancement_rate: float     # 推进率
    test_count: int             # 测试查询数
    passed: bool                # 是否通过


@dataclass
class EvaluationReport:
    """完整评估报告"""
    template_id: str
    counterfactual: CounterfactualResult
    action_advancement: AdvancementResult
    overall_pass: bool
    can_deploy: bool


class TemplateEvaluator:
    """
    模板评估器
    
    两种评估方法：
    1. 反事实对比（Counterfactual）：测角色真实贡献
    2. 结果导向（Action Advancement）：测任务推进效果
    """
    
    # 评估阈值
    CF_MEAN_THRESHOLD = 10.0      # 反事实平均贡献 > 10 分
    CF_MIN_THRESHOLD = 0.0        # 最小贡献 > 0
    AA_RATE_THRESHOLD = 0.7       # 推进率 ≥ 70%
    
    def __init__(self, golden_dataset: Optional[List[Dict]] = None):
        """
        Args:
            golden_dataset: 黄金数据集（人工标注的标准答案）
        """
        self.golden_dataset = golden_dataset or []
    
    def evaluate(self, template_id: str) -> EvaluationReport:
        """
        完整评估流程
        
        Args:
            template_id: 要评估的模板 ID
            
        Returns:
            EvaluationReport 包含两项评估结果
        """
        # 1. 反事实对比评估
        cf_result = self.evaluate_counterfactual(template_id)
        
        # 2. Action Advancement 评估
        aa_result = self.evaluate_advancement(template_id)
        
        # 3. 综合判定
        overall_pass = cf_result.passed and aa_result.passed
        
        return EvaluationReport(
            template_id=template_id,
            counterfactual=cf_result,
            action_advancement=aa_result,
            overall_pass=overall_pass,
            can_deploy=overall_pass
        )
    
    def evaluate_counterfactual(
        self, 
        template_id: str,
        test_problems: Optional[List[Dict]] = None,
        baseline_roles: Optional[List[str]] = None
    ) -> CounterfactualResult:
        """
        反事实对比评估
        
        核心逻辑：
        有该角色的系统性能 - 无该角色的系统性能 = 真实贡献
        """
        # 使用黄金数据集前 5 个作为测试
        test_cases = test_problems or self.golden_dataset[:5]
        
        if not test_cases:
            # 无测试数据，返回未通过
            return CounterfactualResult(
                mean_contribution=0.0,
                min_contribution=0.0,
                test_count=0,
                passed=False
            )
        
        contributions = []
        
        for case in test_cases:
            # 模拟：有该角色的系统（实际应调用 CLDFlow）
            score_with = self._simulate_with_role(template_id, case)
            
            # 模拟：无该角色（用通用角色替代）
            score_without = self._simulate_without_role(case, baseline_roles)
            
            contribution = score_with - score_without
            contributions.append(contribution)
        
        mean_contrib = mean(contributions) if contributions else 0.0
        min_contrib = min(contributions) if contributions else 0.0
        
        return CounterfactualResult(
            mean_contribution=mean_contrib,
            min_contribution=min_contrib,
            test_count=len(test_cases),
            passed=(mean_contrib > self.CF_MEAN_THRESHOLD and 
                   min_contrib > self.CF_MIN_THRESHOLD)
        )
    
    def evaluate_advancement(
        self,
        template_id: str,
        test_queries: Optional[List[str]] = None
    ) -> AdvancementResult:
        """
        Action Advancement 评估
        
        核心逻辑：
        角色在检索任务中是否有效推进（找到变量 + 专业匹配 + 建立因果链）
        """
        # 默认测试查询
        queries = test_queries or self._get_default_test_queries(template_id)
        
        if not queries:
            return AdvancementResult(
                advancement_rate=0.0,
                test_count=0,
                passed=False
            )
        
        advances = 0
        
        for query in queries:
            # 模拟 Agent 执行
            result = self._simulate_agent_execution(template_id, query)
            
            # 检查是否推进（三项标准）
            if self._check_advancement_criteria(result, template_id):
                advances += 1
        
        rate = advances / len(queries) if queries else 0.0
        
        return AdvancementResult(
            advancement_rate=rate,
            test_count=len(queries),
            passed=rate >= self.AA_RATE_THRESHOLD
        )
    
    def _simulate_with_role(self, template_id: str, case: Dict) -> float:
        """模拟：有该角色的系统性能（占位实现）"""
        # Phase 2: 集成真实 CLDFlow 系统
        # 目前返回模拟值
        return 80.0 + hash(template_id) % 20
    
    def _simulate_without_role(self, case: Dict, baseline_roles: Optional[List[str]]) -> float:
        """模拟：无该角色的系统性能（占位实现）"""
        # 通用角色基准性能
        return 60.0
    
    def _simulate_agent_execution(self, template_id: str, query: str) -> Dict:
        """模拟 Agent 执行（占位实现）"""
        # Phase 2: 集成真实 Agent 执行
        return {
            "new_variables": ["var1", "var2"],  # 模拟找到新变量
            "causal_links": [("var1", "var2", "+")],  # 模拟建立因果链
            "domain_match": True  # 模拟专业匹配
        }
    
    def _check_advancement_criteria(self, result: Dict, template_id: str) -> bool:
        """
        检查是否推进（三项标准）
        
        1. 找到新变量？
        2. 变量与角色专业匹配？
        3. 建立有效因果链？
        """
        has_new_vars = len(result.get("new_variables", [])) > 0
        matches_expertise = result.get("domain_match", False)
        has_causal_links = len(result.get("causal_links", [])) > 0
        
        return has_new_vars and matches_expertise and has_causal_links
    
    def _get_default_test_queries(self, template_id: str) -> List[str]:
        """获取默认测试查询"""
        # 根据模板类型返回不同的测试查询
        default_queries = {
            "ddc_320_political": [
                "房产税政策如何影响地方财政？",
                "政府补贴政策对市场的干预效果？",
                "监管改革如何改变行业格局？"
            ],
            "ddc_330_economic": [
                "房价波动的经济驱动因素是什么？",
                "劳动力市场供需如何影响工资？",
                "税收政策对市场效率的影响？"
            ],
            "ddc_340_legal": [
                "新法规如何影响企业合规成本？",
                "司法判例如何塑造行业实践？",
                "监管执法力度对市场的影响？"
            ],
            "ddc_360_social": [
                "住房政策如何影响社会公平？",
                "教育政策对不同群体的差异化影响？",
                "医疗政策如何影响健康不平等？"
            ]
        }
        
        return default_queries.get(template_id, [
            "政策对该领域的影响是什么？",
            "该问题的主要驱动因素有哪些？",
            "不同利益相关者如何受到影响？"
        ])
    
    def get_evaluation_summary(self, report: EvaluationReport) -> Dict:
        """获取评估报告摘要"""
        return {
            "template_id": report.template_id,
            "counterfactual": {
                "mean_contribution": round(report.counterfactual.mean_contribution, 2),
                "min_contribution": round(report.counterfactual.min_contribution, 2),
                "tested": report.counterfactual.test_count > 0,
                "passed": report.counterfactual.passed
            },
            "action_advancement": {
                "advancement_rate": round(report.action_advancement.advancement_rate * 100, 1),
                "tested": report.action_advancement.test_count > 0,
                "passed": report.action_advancement.passed
            },
            "overall_pass": report.overall_pass,
            "can_deploy": report.can_deploy
        }
