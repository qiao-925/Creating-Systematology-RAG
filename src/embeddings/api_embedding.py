"""
API Embedding模型适配器
支持远程API调用（预留接口，暂未实现）
"""

from typing import List, Optional
import requests

from src.embeddings.base import BaseEmbedding
from src.config import config
from src.logger import setup_logger

logger = setup_logger('api_embedding')


class APIEmbedding(BaseEmbedding):
    """远程API模型适配器
    
    注意：当前为预留接口，暂未完整实现
    未来可支持：自建Embedding服务、OpenAI Embeddings、Cohere等
    """
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: str = "default",
        dimension: int = 768,
        timeout: int = 30,
    ):
        """初始化API Embedding
        
        Args:
            api_url: API地址（默认使用配置）
            api_key: API密钥（默认使用配置）
            model_name: 模型名称
            dimension: 向量维度（需要与API返回一致）
            timeout: 请求超时时间（秒）
        """
        self.api_url = api_url or config.EMBEDDING_API_URL
        self.api_key = api_key or getattr(config, 'EMBEDDING_API_KEY', None)
        self.model_name = model_name
        self.dimension = dimension
        self.timeout = timeout
        
        logger.info(f"📡 初始化API Embedding")
        logger.info(f"   API地址: {self.api_url}")
        logger.info(f"   模型: {self.model_name}")
        logger.info(f"   维度: {self.dimension}")
        
        # 验证API可用性（可选）
        self._validate_api()
    
    def _validate_api(self):
        """验证API是否可用（可选）"""
        try:
            # TODO: 实现API健康检查
            # response = requests.get(f"{self.api_url}/health", timeout=5)
            # if response.status_code == 200:
            #     logger.info("✅ API连接正常")
            pass
        except Exception as e:
            logger.warning(f"⚠️  API验证失败: {e}")
    
    def get_query_embedding(self, query: str) -> List[float]:
        """生成查询向量
        
        注意：当前为示例实现，需要根据实际API调整
        """
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # 示例：调用自建Embedding服务
            response = requests.post(
                f"{self.api_url}/embed",
                json={
                    "texts": [query],
                    "model": self.model_name,
                },
                headers=headers,
                timeout=self.timeout,
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 假设API返回格式：{"embeddings": [[...]], "dimension": 768}
            return result["embeddings"][0]
            
        except Exception as e:
            logger.error(f"❌ API调用失败: {e}")
            raise RuntimeError(f"Embedding API调用失败: {e}")
    
    def get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本向量
        
        注意：当前为示例实现，需要根据实际API调整
        """
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # 示例：调用自建Embedding服务
            response = requests.post(
                f"{self.api_url}/embed",
                json={
                    "texts": texts,
                    "model": self.model_name,
                },
                headers=headers,
                timeout=self.timeout,
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 假设API返回格式：{"embeddings": [[...], [...]], "dimension": 768}
            return result["embeddings"]
            
        except Exception as e:
            logger.error(f"❌ API批量调用失败: {e}")
            raise RuntimeError(f"Embedding API批量调用失败: {e}")
    
    def get_embedding_dimension(self) -> int:
        """获取向量维度"""
        return self.dimension
    
    def get_model_name(self) -> str:
        """获取模型名称"""
        return self.model_name


# 预留：OpenAI Embeddings适配器
class OpenAIEmbedding(APIEmbedding):
    """OpenAI Embeddings适配器（预留）
    
    未来可支持：text-embedding-ada-002等
    """
    
    def __init__(self, api_key: str, model: str = "text-embedding-ada-002"):
        super().__init__(
            api_url="https://api.openai.com/v1",
            api_key=api_key,
            model_name=model,
            dimension=1536,  # ada-002维度
        )
        logger.info("📡 初始化OpenAI Embeddings（预留接口）")
    
    # TODO: 实现OpenAI特定的API调用逻辑


# 预留：Cohere Embeddings适配器
class CohereEmbedding(APIEmbedding):
    """Cohere Embeddings适配器（预留）
    
    未来可支持：embed-english-v3.0等
    """
    
    def __init__(self, api_key: str, model: str = "embed-english-v3.0"):
        super().__init__(
            api_url="https://api.cohere.ai/v1",
            api_key=api_key,
            model_name=model,
            dimension=1024,  # v3.0维度
        )
        logger.info("📡 初始化Cohere Embeddings（预留接口）")
    
    # TODO: 实现Cohere特定的API调用逻辑

