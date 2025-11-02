"""
RAGAS评估器观察器

使用RAGAS框架进行RAG系统评估
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from src.observers.base import BaseObserver, ObserverType
from src.config import config
from src.logger import setup_logger

logger = setup_logger('ragas_evaluator')


class RAGASEvaluator(BaseObserver):
    """RAGAS评估器观察器
    
    使用RAGAS框架进行RAG系统评估
    支持多维度评估指标：
    - faithfulness（忠实度）
    - context_precision（上下文精确度）
    - context_recall（上下文召回率）
    - answer_relevancy（答案相关性）
    - context_relevancy（上下文相关性）
    """
    
    def __init__(
        self,
        name: str = "ragas_evaluator",
        enabled: bool = True,
        metrics: Optional[List[str]] = None,
        batch_size: int = 10,
    ):
        """初始化RAGAS评估器
        
        Args:
            name: 观察器名称
            enabled: 是否启用
            metrics: 评估指标列表（默认使用所有指标）
            batch_size: 批量评估大小
        """
        super().__init__(name, enabled)
        self.metrics = metrics or [
            "faithfulness",
            "context_precision",
            "context_recall",
            "answer_relevancy",
            "context_relevancy",
        ]
        self.batch_size = batch_size
        
        # 评估数据存储
        self.evaluation_data: List[Dict[str, Any]] = []
        self.evaluation_results: List[Dict[str, Any]] = []
        
        # RAGAS相关对象
        self.dataset = None
        
        if self.enabled:
            self.setup()
    
    def get_observer_type(self) -> ObserverType:
        return ObserverType.EVALUATION
    
    def setup(self) -> None:
        """设置RAGAS评估器"""
        logger.info("📊 初始化 RAGAS 评估器")
        
        try:
            # 延迟导入RAGAS（因为它是可选依赖）
            import ragas
            from ragas import evaluate
            from ragas.datasets_schema import Dataset
            
            self.ragas = ragas
            self.evaluate = evaluate
            self.Dataset = Dataset
            
            logger.info(f"✅ RAGAS 评估器已初始化")
            logger.info(f"   评估指标: {', '.join(self.metrics)}")
            
        except ImportError as e:
            logger.warning(f"⚠️  RAGAS 未安装: {e}")
            logger.info("   请运行: pip install ragas")
            logger.info("   观察器将被禁用")
            self.enabled = False
        except Exception as e:
            logger.error(f"❌ RAGAS 初始化失败: {e}")
            self.enabled = False
    
    def on_query_start(self, query: str, **kwargs) -> Optional[str]:
        """查询开始时回调"""
        if not self.enabled:
            return None
        
        # 记录查询开始时间
        self.current_query_start = datetime.now()
        logger.debug(f"🔍 RAGAS 记录查询: {query[:50]}...")
        return None
    
    def on_query_end(
        self,
        query: str,
        answer: str,
        sources: List[Dict],
        trace_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """查询结束时回调"""
        if not self.enabled:
            return
        
        try:
            # 提取上下文
            contexts = []
            for source in sources:
                if isinstance(source, dict):
                    # 从source中提取文本
                    context_text = source.get('text', '') or source.get('content', '')
                    if context_text:
                        contexts.append(context_text)
                elif hasattr(source, 'text'):
                    contexts.append(source.text)
            
            # 记录评估数据
            evaluation_entry = {
                "question": query,
                "answer": answer,
                "contexts": contexts,
                "ground_truth": kwargs.get('ground_truth', None),  # 可选的真值
                "timestamp": datetime.now().isoformat(),
                "trace_id": trace_id,
            }
            
            self.evaluation_data.append(evaluation_entry)
            logger.debug(f"✅ RAGAS 记录查询完成: {len(contexts)} 个上下文")
            
            # 如果达到批量大小，执行批量评估
            if len(self.evaluation_data) >= self.batch_size:
                self._run_batch_evaluation()
                
        except Exception as e:
            logger.warning(f"⚠️  RAGAS 记录查询失败: {e}")
    
    def on_retrieval(self, query: str, nodes: List[Any], **kwargs) -> None:
        """检索完成时回调（可选）"""
        if not self.enabled:
            return
        
        # 可以在这里记录检索相关的信息
        logger.debug(f"📚 RAGAS 记录检索: {len(nodes)} 个节点")
    
    def _run_batch_evaluation(self) -> None:
        """执行批量评估"""
        if not self.enabled or not self.evaluation_data:
            return
        
        try:
            logger.info(f"📊 开始批量评估: {len(self.evaluation_data)} 条数据")
            
            # 准备数据集
            dataset_dict = {
                "question": [entry["question"] for entry in self.evaluation_data],
                "answer": [entry["answer"] for entry in self.evaluation_data],
                "contexts": [entry["contexts"] for entry in self.evaluation_data],
            }
            
            # 如果有ground_truth，添加到数据集
            if any(entry.get("ground_truth") for entry in self.evaluation_data):
                dataset_dict["ground_truth"] = [
                    entry.get("ground_truth", "") for entry in self.evaluation_data
                ]
            
            # 创建数据集
            dataset = self.Dataset.from_dict(dataset_dict)
            
            # 执行评估
            result = self.evaluate(
                dataset=dataset,
                metrics=self.metrics,
            )
            
            # 保存结果
            evaluation_result = {
                "timestamp": datetime.now().isoformat(),
                "data_count": len(self.evaluation_data),
                "metrics": result.to_dict() if hasattr(result, 'to_dict') else str(result),
                "raw_result": result,
            }
            
            self.evaluation_results.append(evaluation_result)
            logger.info(f"✅ 批量评估完成: {len(self.evaluation_data)} 条数据")
            
            # 打印评估结果摘要
            if hasattr(result, '__dict__'):
                logger.info(f"📊 评估结果摘要:")
                for metric_name in self.metrics:
                    if hasattr(result, metric_name):
                        metric_value = getattr(result, metric_name)
                        logger.info(f"   {metric_name}: {metric_value}")
            
            # 清空已评估的数据
            self.evaluation_data.clear()
            
        except Exception as e:
            logger.error(f"❌ RAGAS 批量评估失败: {e}")
            logger.exception(e)
    
    def evaluate_all(self) -> Optional[Dict[str, Any]]:
        """评估所有已收集的数据
        
        Returns:
            评估结果字典
        """
        if not self.enabled:
            return None
        
        if not self.evaluation_data:
            logger.warning("⚠️  没有待评估的数据")
            return None
        
        # 执行最后一次批量评估
        self._run_batch_evaluation()
        
        if not self.evaluation_results:
            return None
        
        # 返回最新的评估结果
        return self.evaluation_results[-1] if self.evaluation_results else None
    
    def get_report(self) -> Dict[str, Any]:
        """获取评估报告"""
        report = {
            "observer_type": "ragas_evaluator",
            "enabled": self.enabled,
            "metrics": self.metrics,
            "pending_evaluations": len(self.evaluation_data),
            "completed_evaluations": len(self.evaluation_results),
            "latest_result": self.evaluation_results[-1] if self.evaluation_results else None,
        }
        
        return report
    
    def teardown(self) -> None:
        """清理资源"""
        if not self.enabled:
            return
        
        # 如果有未评估的数据，执行最后一次评估
        if self.evaluation_data:
            logger.info(f"📊 清理前执行最后一次评估: {len(self.evaluation_data)} 条数据")
            self._run_batch_evaluation()
        
        logger.info("✅ RAGAS 评估器已清理")

