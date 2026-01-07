"""
RAG 引擎核心数据模型：定义查询、检索、结果等核心数据结构

主要功能：
- QueryContext：查询上下文模型（包含查询、用户、会话等信息）
- QueryResult：查询结果模型（包含答案、来源、推理链等）
- RetrievalResult：检索结果模型（包含检索到的节点列表）
- NodeWithScoreModel：带分数的节点模型（Pydantic 包装）

特性：
- 类型安全的数据验证
- 清晰的字段定义和验证规则
- 便于序列化和反序列化
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class NodeWithScoreModel(BaseModel):
    """带分数的节点模型
    
    用于表示检索到的文档节点及其相似度分数
    """
    text: str = Field(..., description="节点文本内容")
    score: float = Field(..., ge=0.0, le=1.0, description="相似度分数（0-1）")
    node_id: str = Field(..., description="节点唯一标识符")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="节点元数据")
    
    @classmethod
    def from_llama_node(cls, node_with_score) -> "NodeWithScoreModel":
        """从 LlamaIndex NodeWithScore 创建模型
        
        Args:
            node_with_score: LlamaIndex 的 NodeWithScore 对象
            
        Returns:
            NodeWithScoreModel 实例
        """
        node = node_with_score.node if hasattr(node_with_score, 'node') else node_with_score
        score = node_with_score.score if hasattr(node_with_score, 'score') else 0.0
        
        return cls(
            text=node.text if hasattr(node, 'text') else str(node),
            score=float(score),
            node_id=node.node_id if hasattr(node, 'node_id') else str(node.id_) if hasattr(node, 'id_') else "",
            metadata=node.metadata if hasattr(node, 'metadata') else {}
        )


class RetrievalResult(BaseModel):
    """检索结果模型
    
    表示一次检索操作的结果，包含检索到的节点列表和检索策略信息
    """
    nodes: List[NodeWithScoreModel] = Field(..., description="检索到的节点列表")
    strategy: str = Field(..., description="使用的检索策略（vector/bm25/hybrid/grep/multi）")
    query: str = Field(..., description="查询文本")
    total_count: int = Field(..., ge=0, description="总结果数")
    
    @property
    def has_results(self) -> bool:
        """是否有检索结果"""
        return len(self.nodes) > 0
    
    @field_validator('strategy')
    def validate_strategy(cls, v: str) -> str:
        """验证检索策略"""
        valid_strategies = ["vector", "bm25", "hybrid", "grep", "multi"]
        if v not in valid_strategies:
            raise ValueError(f"无效的检索策略: {v}。有效值: {valid_strategies}")
        return v


class QueryContext(BaseModel):
    """查询上下文模型
    
    包含查询所需的所有上下文信息，用于在 RAG 流程中传递
    """
    query: str = Field(..., min_length=1, description="原始查询文本")
    processed_query: Optional[str] = Field(None, description="处理后的查询文本（经过意图理解、改写等）")
    user_id: Optional[str] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    strategy: str = Field(default="vector", description="检索策略")
    top_k: int = Field(default=3, ge=1, le=50, description="检索数量")
    similarity_cutoff: Optional[float] = Field(None, ge=0.0, le=1.0, description="相似度阈值")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="上下文元数据")
    
    @field_validator('query')
    def validate_query(cls, v: str) -> str:
        """验证查询文本"""
        v = v.strip()
        if not v:
            raise ValueError('查询文本不能为空')
        return v
    
    @field_validator('strategy')
    def validate_strategy(cls, v: str) -> str:
        """验证检索策略"""
        valid_strategies = ["vector", "bm25", "hybrid", "grep", "multi"]
        if v not in valid_strategies:
            raise ValueError(f"无效的检索策略: {v}。有效值: {valid_strategies}")
        return v


class SourceModel(BaseModel):
    """引用来源模型
    
    用于表示答案的引用来源，包含来源文本、相似度分数等信息
    """
    text: str = Field(..., description="来源文本")
    score: float = Field(..., ge=0.0, le=1.0, description="相似度分数（0-1）")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="来源元数据")
    file_name: Optional[str] = Field(None, description="文件名")
    page_number: Optional[int] = Field(None, ge=1, description="页码")
    node_id: Optional[str] = Field(None, description="节点ID")
    
    @classmethod
    def from_node_with_score(cls, node_with_score) -> "SourceModel":
        """从 NodeWithScoreModel 创建 SourceModel
        
        Args:
            node_with_score: NodeWithScoreModel 实例
            
        Returns:
            SourceModel 实例
        """
        metadata = node_with_score.metadata.copy()
        file_name = metadata.get('file_name') or metadata.get('filename')
        page_number = metadata.get('page_number') or metadata.get('page')
        
        return cls(
            text=node_with_score.text,
            score=node_with_score.score,
            metadata=metadata,
            file_name=file_name,
            page_number=page_number,
            node_id=node_with_score.node_id
        )


class QueryResult(BaseModel):
    """查询结果模型
    
    表示一次完整查询的结果，包含答案、来源、推理链等信息
    """
    answer: str = Field(..., min_length=1, description="生成的答案")
    sources: List[SourceModel] = Field(default_factory=list, description="引用来源列表")
    reasoning_content: Optional[str] = Field(None, description="推理链内容（DeepSeek reasoning）")
    trace_info: Optional[Dict[str, Any]] = Field(None, description="追踪信息")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="结果元数据")
    
    @property
    def has_sources(self) -> bool:
        """是否有引用来源"""
        return len(self.sources) > 0
    
    @field_validator('answer')
    def validate_answer(cls, v: str) -> str:
        """验证答案"""
        v = v.strip()
        if not v:
            raise ValueError('答案不能为空')
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "answer": self.answer,
            "sources": [source.model_dump() for source in self.sources],
            "reasoning_content": self.reasoning_content,
            "trace_info": self.trace_info,
            "metadata": self.metadata
        }
