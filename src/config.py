"""
配置管理模块
管理API密钥、模型配置、路径配置等
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """应用配置类"""
    
    def __init__(self):
        # 项目根目录
        self.PROJECT_ROOT = Path(__file__).parent.parent
        
        # DeepSeek API配置
        self.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
        self.DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
        
        # 模型配置
        self.LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
        self.EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-zh-v1.5")
        
        # HuggingFace镜像配置
        self.HF_ENDPOINT = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")
        self.HF_OFFLINE_MODE = os.getenv("HF_OFFLINE_MODE", "false").lower() == "true"
        
        # 向量数据库配置
        self.VECTOR_STORE_PATH = self._get_path("VECTOR_STORE_PATH", "vector_store")
        self.CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "systematology_docs")
        
        # 文档路径配置
        self.RAW_DATA_PATH = self._get_path("RAW_DATA_PATH", "data/raw")
        self.PROCESSED_DATA_PATH = self._get_path("PROCESSED_DATA_PATH", "data/processed")
        
        # 会话和日志路径配置
        self.SESSIONS_PATH = self._get_path("SESSIONS_PATH", "sessions")
        self.ACTIVITY_LOG_PATH = self._get_path("ACTIVITY_LOG_PATH", "logs/activity")
        
        # GitHub 配置
        self.GITHUB_REPOS_PATH = self._get_path("GITHUB_REPOS_PATH", "data/github_repos")
        self.GITHUB_METADATA_PATH = self._get_path("GITHUB_METADATA_PATH", "data/github_metadata.json")
        
        # 索引配置
        self.CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
        self.CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
        self.SIMILARITY_TOP_K = int(os.getenv("SIMILARITY_TOP_K", "3"))
        
        # 应用配置
        self.APP_TITLE = os.getenv("APP_TITLE", "系统科学知识库RAG")
        self.APP_PORT = int(os.getenv("APP_PORT", "8501"))
        
        # GitHub数据源配置
        # 注意：GITHUB_TOKEN 现在是用户级别的配置，不再从环境变量读取
        # 每个用户在 UI 中配置自己的 Token，存储在用户数据中
        self.GITHUB_DEFAULT_BRANCH = os.getenv("GITHUB_DEFAULT_BRANCH", "main")
        
        # 维基百科配置
        self.ENABLE_WIKIPEDIA = os.getenv("ENABLE_WIKIPEDIA", "true").lower() == "true"
        self.WIKIPEDIA_AUTO_LANG = os.getenv("WIKIPEDIA_AUTO_LANG", "true").lower() == "true"
        self.WIKIPEDIA_THRESHOLD = float(os.getenv("WIKIPEDIA_THRESHOLD", "0.6"))
        self.WIKIPEDIA_MAX_RESULTS = int(os.getenv("WIKIPEDIA_MAX_RESULTS", "2"))
        self.WIKIPEDIA_PRELOAD_CONCEPTS = [
            concept.strip() 
            for concept in os.getenv(
                "WIKIPEDIA_PRELOAD_CONCEPTS",
                "系统科学,钱学森,系统工程,控制论,信息论"
            ).split(',')
            if concept.strip()
        ]
        
    def _get_path(self, env_var: str, default: str) -> Path:
        """获取路径配置，支持相对路径和绝对路径"""
        path_str = os.getenv(env_var, default)
        path = Path(path_str)
        
        # 如果是相对路径，则相对于项目根目录
        if not path.is_absolute():
            path = self.PROJECT_ROOT / path
            
        return path
    
    def ensure_directories(self):
        """确保所有必要的目录存在"""
        directories = [
            self.VECTOR_STORE_PATH,
            self.RAW_DATA_PATH,
            self.PROCESSED_DATA_PATH,
            self.SESSIONS_PATH,
            self.ACTIVITY_LOG_PATH,
            self.GITHUB_REPOS_PATH,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
    def validate(self) -> tuple[bool, Optional[str]]:
        """验证配置是否完整
        
        Returns:
            (is_valid, error_message)
        """
        if not self.DEEPSEEK_API_KEY:
            return False, "未设置DEEPSEEK_API_KEY环境变量"
        
        if self.CHUNK_SIZE <= 0:
            return False, "CHUNK_SIZE必须大于0"
            
        if self.CHUNK_OVERLAP < 0:
            return False, "CHUNK_OVERLAP必须大于等于0"
            
        if self.CHUNK_OVERLAP >= self.CHUNK_SIZE:
            return False, "CHUNK_OVERLAP必须小于CHUNK_SIZE"
            
        return True, None
    
    def __repr__(self) -> str:
        """返回配置的字符串表示（隐藏敏感信息）"""
        return f"""Config(
    PROJECT_ROOT={self.PROJECT_ROOT},
    DEEPSEEK_API_BASE={self.DEEPSEEK_API_BASE},
    LLM_MODEL={self.LLM_MODEL},
    EMBEDDING_MODEL={self.EMBEDDING_MODEL},
    HF_ENDPOINT={self.HF_ENDPOINT},
    HF_OFFLINE_MODE={self.HF_OFFLINE_MODE},
    VECTOR_STORE_PATH={self.VECTOR_STORE_PATH},
    SESSIONS_PATH={self.SESSIONS_PATH},
    ACTIVITY_LOG_PATH={self.ACTIVITY_LOG_PATH},
    GITHUB_METADATA_PATH={self.GITHUB_METADATA_PATH},
    CHUNK_SIZE={self.CHUNK_SIZE},
    CHUNK_OVERLAP={self.CHUNK_OVERLAP},
    SIMILARITY_TOP_K={self.SIMILARITY_TOP_K},
    GITHUB_DEFAULT_BRANCH={self.GITHUB_DEFAULT_BRANCH},
    ENABLE_WIKIPEDIA={self.ENABLE_WIKIPEDIA},
    WIKIPEDIA_THRESHOLD={self.WIKIPEDIA_THRESHOLD},
    WIKIPEDIA_MAX_RESULTS={self.WIKIPEDIA_MAX_RESULTS}
)"""


# 全局配置实例
config = Config()


if __name__ == "__main__":
    # 测试配置
    print("=== 配置信息 ===")
    print(config)
    print("\n=== 配置验证 ===")
    is_valid, error_msg = config.validate()
    if is_valid:
        print("✅ 配置验证通过")
        config.ensure_directories()
        print("✅ 目录创建成功")
    else:
        print(f"❌ 配置验证失败: {error_msg}")

