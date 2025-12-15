"""
Hugging Face Inference API Embedding适配器：支持通过HF Inference Providers调用embedding模型

主要功能：
- HFInferenceEmbedding类：Hugging Face Inference API适配器，实现BaseEmbedding接口
- get_query_embedding()：通过HF Inference API生成查询向量
- get_text_embeddings()：通过HF Inference API批量生成文本向量

特性：
- 使用直接HTTP请求（requests）调用HF Inference API，提高透明度和可调试性
- 支持按量付费（PRO用户每月有$2.00免费额度）
- 统一的错误处理和重试机制
"""

import os
from typing import List, Optional
import time
import asyncio
import threading
import json
import weakref
from concurrent.futures import ThreadPoolExecutor

import requests
from requests.exceptions import RequestException

from src.infrastructure.embeddings.base import BaseEmbedding
from src.infrastructure.config import config
from src.infrastructure.logger import get_logger

logger = get_logger('hf_inference_embedding')

# 全局线程池执行器，用于 asyncio.to_thread()
# 使用弱引用集合跟踪所有 HFInferenceEmbedding 实例，以便在退出时清理
_global_executor: Optional[ThreadPoolExecutor] = None
_embedding_instances: weakref.WeakSet = weakref.WeakSet()


def _get_or_create_executor() -> ThreadPoolExecutor:
    """获取或创建全局线程池执行器
    
    Returns:
        ThreadPoolExecutor: 全局线程池执行器
    """
    global _global_executor
    if _global_executor is None:
        # 创建线程池，最大线程数为 CPU 核心数的 2 倍
        max_workers = min(32, (os.cpu_count() or 1) * 2)
        _global_executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="hf_embedding")
        logger.debug(f"创建全局线程池执行器: max_workers={max_workers}")
    return _global_executor


def cleanup_hf_embedding_resources() -> None:
    """清理所有 HFInferenceEmbedding 资源和线程池
    
    应该在应用退出时调用此函数，确保所有线程和连接被正确关闭。
    """
    global _global_executor
    
    logger.info("🔧 开始清理 Hugging Face Embedding 资源...")
    
    # 1. 关闭所有 HFInferenceEmbedding 实例
    instances_to_close = list(_embedding_instances)
    if instances_to_close:
        logger.info(f"关闭 {len(instances_to_close)} 个 HFInferenceEmbedding 实例...")
        for instance in instances_to_close:
            try:
                instance.close()
            except Exception as e:
                logger.warning(f"关闭 HFInferenceEmbedding 实例时出错: {e}")
    
    # 2. 关闭全局线程池执行器
    if _global_executor is not None:
        try:
            logger.info("关闭全局线程池执行器...")
            _global_executor.shutdown(wait=True, timeout=5.0)
            logger.info("✅ 全局线程池执行器已关闭")
        except Exception as e:
            logger.warning(f"关闭线程池执行器时出错: {e}")
        finally:
            _global_executor = None
    
    logger.info("✅ Hugging Face Embedding 资源清理完成")


class TimeMonitor:
    """时间监控上下文管理器，用于实时记录操作耗时
    
    使用后台线程每秒打印一次已花费时间，帮助监控长时间运行的操作。
    """
    
    def __init__(
        self,
        logger_instance,
        message_template: str,
        interval: float = 5.0
    ):
        """初始化时间监控器
        
        Args:
            logger_instance: logger 实例
            message_template: 日志消息模板，支持 {elapsed} 占位符
            interval: 打印间隔（秒），默认5.0秒
        """
        self.logger = logger_instance
        self.message_template = message_template
        self.interval = interval
        self.start_time: Optional[float] = None
        self.stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None
    
    def __enter__(self):
        """进入上下文，开始监控"""
        self.start_time = time.time()
        self.stop_event.clear()
        
        # 创建并启动后台线程
        self.thread = threading.Thread(
            target=self._log_elapsed_time,
            daemon=True  # 设置为守护线程，主线程退出时自动结束
        )
        self.thread.start()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文，停止监控"""
        # 停止后台线程
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            # 等待线程结束，最多等待2秒
            self.thread.join(timeout=2.0)
            # 如果线程仍在运行，强制终止（daemon 线程会在主线程退出时自动终止）
            if self.thread.is_alive():
                self.logger.debug("TimeMonitor 线程仍在运行，将在主线程退出时自动终止")
        
        # 计算总耗时
        if self.start_time is not None:
            total_elapsed = time.time() - self.start_time
            # 如果总耗时大于0.1秒，打印最终日志
            if total_elapsed >= 0.1:
                final_message = self.message_template.format(elapsed=int(total_elapsed))
                self.logger.info(f"{final_message} (总计)")
        
        return False  # 不抑制异常
    
    def _log_elapsed_time(self):
        """后台线程函数，每5秒打印一次已花费时间"""
        last_logged_interval = -1
        
        while not self.stop_event.is_set():
            if self.start_time is None:
                break
            
            elapsed = time.time() - self.start_time
            current_interval = int(elapsed / self.interval)  # 按间隔计算
            
            # 只在间隔变化时打印，避免重复
            if current_interval > last_logged_interval and current_interval > 0:
                try:
                    elapsed_seconds = int(elapsed)
                    message = self.message_template.format(elapsed=elapsed_seconds)
                    self.logger.info(message)
                    last_logged_interval = current_interval
                except Exception as e:
                    # 如果格式化失败，记录错误但不中断监控
                    self.logger.debug(f"时间监控日志格式化失败: {e}")
            
            # 等待间隔时间或直到停止事件被设置
            self.stop_event.wait(timeout=self.interval)


class HFInferenceEmbedding(BaseEmbedding):
    """Hugging Face Inference API Embedding 适配器
    
    使用 Hugging Face Inference Providers 服务调用 embedding 模型
    支持按量付费，PRO 用户每月有 $2.00 免费额度
    """
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-base-zh-v1.5",
        api_key: Optional[str] = None,
    ):
        """初始化 HF Inference API Embedding
        
        Args:
            model_name: Hugging Face 模型名称（默认 BAAI/bge-base-zh-v1.5）
            api_key: Hugging Face API Token（从环境变量 HF_TOKEN 或配置读取）
        """
        self.model_name = model_name
        self._dimension: Optional[int] = None
        self._closed = False
        self._active_requests: set = set()  # 跟踪正在进行的请求
        
        # 获取 API key（优先级：参数 > 环境变量 > 配置）
        self.api_key = api_key or os.getenv("HF_TOKEN") or getattr(config, 'HF_TOKEN', None)
        
        if not self.api_key:
            raise ValueError(
                "HF_TOKEN 未设置。请设置环境变量 HF_TOKEN 或配置中的 HF_TOKEN。"
                "获取 Token: https://huggingface.co/settings/tokens"
            )
        
        # 构建 API URL 和 headers（使用直接 HTTP 请求）
        self.api_url = f"https://router.huggingface.co/hf-inference/models/{self.model_name}/pipeline/feature-extraction"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # 注册到全局实例集合，以便在退出时清理
        _embedding_instances.add(self)
        
        logger.info(f"📡 初始化 Hugging Face Inference API Embedding: {self.model_name}")
    
    def _get_default_dimension(self, model_name: str) -> int:
        """根据模型名称获取默认维度"""
        model_lower = model_name.lower()
        if "qwen" in model_lower and ("0.6b" in model_lower or "8b" in model_lower):
            return 1024
        elif "bge" in model_lower:
            return 768 if "base" in model_lower else 384
        return 384  # 通用默认值
    
    def _make_request(self, texts: List[str], retry_count: int = 0) -> List[List[float]]:
        """发起 API 请求（带重试机制）
        
        使用 HuggingFace Inference API 的 feature_extraction 方法生成向量。
        注意：feature_extraction 一次只能处理一个文本，需要逐个处理。
        
        Args:
            texts: 文本列表
            retry_count: 当前重试次数
            
        Returns:
            向量列表
            
        Raises:
            RuntimeError: API 调用失败或实例已关闭
        """
        # 检查实例是否已关闭
        if self._closed:
            raise RuntimeError(f"HFInferenceEmbedding 实例已关闭，无法继续请求")
        
        if retry_count > 0:
            logger.warning(f"⚠️  重试请求 ({retry_count}/3): 模型={self.model_name}, 文本数量={len(texts)}")
        else:
            logger.debug(f"📤 HF Inference API 请求: 模型={self.model_name}, 文本数量={len(texts)}")
        
        # 创建请求标识符用于跟踪
        request_id = id(texts)
        self._active_requests.add(request_id)
        
        try:
            # 批次总时间监控
            with TimeMonitor(
                logger,
                f"⏱️  HF Inference API 调用进行中: 已花费 {{elapsed}} 秒 (模型={self.model_name}, 文本数量={len(texts)})"
            ):
                try:
                    results = []
                    total = len(texts)
                    
                    # feature_extraction 一次只能处理一个文本，逐个处理
                    for idx, text in enumerate(texts):
                        # 每个文本处理时间监控
                        with TimeMonitor(
                            logger,
                            f"⏱️  处理文本 {idx + 1}/{total}: 已花费 {{elapsed}} 秒"
                        ):
                            # 构建请求 payload
                            payload = {"inputs": text}
                            
                            # 记录请求信息（curl 命令格式）
                            logger.info(f"📤 发送 HTTP 请求:")
                            logger.info(f"   URL: {self.api_url}")
                            logger.info(f"   Method: POST")
                            logger.info(f"   Headers: {json.dumps({k: v if k != 'Authorization' else 'Bearer ***' for k, v in self.headers.items()}, ensure_ascii=False, indent=2)}")
                            logger.info(f"   Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
                            
                            # 生成 curl 命令（用于调试，隐藏密钥）
                            curl_command = (
                                f"curl -X POST '{self.api_url}' \\\n"
                                f"  -H 'Authorization: Bearer $HF_TOKEN' \\\n"
                                f"  -H 'Content-Type: application/json' \\\n"
                                f"  -d '{json.dumps(payload, ensure_ascii=False)}'"
                            )
                            logger.info(f"   📋 curl 命令 (使用环境变量 HF_TOKEN):\n{curl_command}")
                            
                            # 检查是否已关闭（在请求前再次检查）
                            if self._closed:
                                raise RuntimeError("HFInferenceEmbedding 实例已关闭，请求被取消")
                            
                            # 使用直接 HTTP 请求调用 API
                            request_start = time.time()
                            try:
                                response = requests.post(
                                    self.api_url,
                                    headers=self.headers,
                                    json=payload,
                                    timeout=30,
                                )
                            except requests.exceptions.RequestException as e:
                                # 如果已关闭，不重试
                                if self._closed:
                                    raise RuntimeError("HFInferenceEmbedding 实例已关闭，请求被取消") from e
                                raise
                            request_elapsed = time.time() - request_start
                            
                            # 记录响应信息
                            logger.info(f"📥 收到 HTTP 响应:")
                            logger.info(f"   状态码: {response.status_code}")
                            logger.info(f"   响应时间: {request_elapsed:.2f} 秒")
                            logger.info(f"   Headers: {dict(response.headers)}")
                            
                            response.raise_for_status()  # 自动处理 HTTP 错误
                            
                            # 解析响应
                            try:
                                result = response.json()
                                # 记录响应数据（限制长度，避免日志过长）
                                result_str = json.dumps(result, ensure_ascii=False)
                                if len(result_str) > 1000:
                                    logger.info(f"   响应数据 (前1000字符): {result_str[:1000]}...")
                                    logger.info(f"   响应数据长度: {len(result_str)} 字符")
                                    if isinstance(result, list) and len(result) > 0:
                                        logger.info(f"   向量维度: {len(result)}")
                                        logger.info(f"   向量前5个值: {result[:5]}")
                                        logger.info(f"   向量后5个值: {result[-5:]}")
                                else:
                                    logger.info(f"   响应数据: {result_str}")
                                
                                # 处理响应格式并转换为列表
                                if isinstance(result, list):
                                    # 直接是向量列表
                                    embedding = [float(x) for x in result]
                                elif isinstance(result, dict):
                                    # 可能是包装在字典中的格式
                                    if "embeddings" in result:
                                        embedding = [float(x) for x in result["embeddings"]]
                                    elif "output" in result:
                                        embedding = [float(x) for x in result["output"]]
                                    else:
                                        # 尝试直接使用第一个值
                                        first_key = next(iter(result.values()))
                                        if isinstance(first_key, list):
                                            embedding = [float(x) for x in first_key]
                                        else:
                                            embedding = [float(first_key)]
                                else:
                                    # 单个值或其他格式
                                    embedding = [float(result)] if not isinstance(result, list) else [float(x) for x in result]
                                
                                results.append(embedding)
                                
                                # 批量处理时显示进度
                                if total > 1 and (idx + 1) % 10 == 0:
                                    logger.debug(f"   进度: {idx + 1}/{total}")
                            except json.JSONDecodeError as e:
                                logger.error(f"   ❌ JSON 解析失败: {e}")
                                logger.error(f"   响应文本: {response.text[:500]}")
                                raise
                    
                    if total > 1:
                        logger.debug(f"📥 批量处理完成: {len(results)}/{total} 个文本")
                    
                    return results
                            
                except RequestException as e:
                    # 统一错误处理：全部重试
                    return self._handle_request_error(e, texts, retry_count)
                except Exception as e:
                    # 处理其他异常（如 JSON 解析错误等）
                    return self._handle_request_error(e, texts, retry_count)
        finally:
            # 移除请求跟踪
            self._active_requests.discard(request_id)
    
    def _handle_request_error(
        self,
        error: Exception,
        texts: List[str],
        retry_count: int
    ) -> List[List[float]]:
        """处理 API 请求错误（统一重试策略）
        
        Args:
            error: 捕获的异常
            texts: 请求的文本列表
            retry_count: 当前重试次数
            
        Returns:
            向量列表（重试成功时）
            
        Raises:
            RuntimeError: 重试次数用尽
        """
        max_retries = 3
        
        # 构建详细的错误信息
        error_details = str(error)
        if isinstance(error, RequestException):
            if hasattr(error, 'response') and error.response is not None:
                try:
                    error_body = error.response.text[:200]  # 限制长度
                    error_details = f"HTTP {error.response.status_code}: {error_body}"
                except Exception:
                    error_details = f"HTTP {error.response.status_code}: {str(error)}"
        
        if retry_count < max_retries:
            wait_time = (retry_count + 1) * 1.0
            logger.warning(
                f"❌ API 请求失败: {error.__class__.__name__}: {error_details}。"
                f"{wait_time:.1f}秒后重试 ({retry_count + 1}/{max_retries})"
            )
            time.sleep(wait_time)
            return self._make_request(texts, retry_count + 1)
        else:
            logger.error(f"❌ API 调用失败（已重试 {max_retries} 次）: {error_details}")
            raise RuntimeError(
                f"Hugging Face Inference API 调用失败（模型: {self.model_name}）: {error_details}"
            ) from error
    
    def get_query_embedding(self, query: str) -> List[float]:
        """生成查询向量"""
        embeddings = self.get_text_embeddings([query])
        return embeddings[0]
    
    def get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本向量
        
        支持批量处理，自动分批以避免单次请求过大。
        由于 feature_extraction 一次只能处理一个文本，内部会逐个处理。
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表，每个文本对应一个向量
        """
        if not texts:
            return []
        
        # 分批处理，每批最多 100 个文本
        batch_size = 100
        total_batches = (len(texts) + batch_size - 1) // batch_size
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            if total_batches > 1:
                logger.debug(f"处理批次 {batch_num}/{total_batches} ({len(batch)} 个文本)")
            
            batch_embeddings = self._make_request(batch)
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    def get_embedding_dimension(self) -> int:
        """获取向量维度（确保总是返回有效值）"""
        if self._dimension is None:
            self._dimension = self._get_default_dimension(self.model_name)
            logger.debug(f"使用默认维度: {self._dimension}")
            try:
                test_embedding = self.get_query_embedding("test")
                detected_dim = len(test_embedding)
                if detected_dim != self._dimension:
                    logger.info(f"🔄 检测到实际维度 {detected_dim}，更新默认值 {self._dimension}")
                    self._dimension = detected_dim
            except Exception as e:
                logger.warning(f"⚠️  无法通过API获取维度，使用默认值: {e}")
        return self._dimension
    
    def get_model_name(self) -> str:
        """获取模型名称"""
        return self.model_name
    
    def close(self) -> None:
        """关闭实例，清理资源
        
        停止所有正在进行的请求，清理线程和连接。
        应该在应用退出时调用此方法。
        """
        if self._closed:
            return
        
        logger.info(f"🔧 开始关闭 HFInferenceEmbedding 实例: {self.model_name}")
        self._closed = True
        
        # 等待正在进行的请求完成（最多等待5秒）
        if self._active_requests:
            logger.debug(f"等待 {len(self._active_requests)} 个正在进行的请求完成...")
            start_wait = time.time()
            while self._active_requests and (time.time() - start_wait) < 5.0:
                time.sleep(0.1)
            
            if self._active_requests:
                logger.warning(f"⚠️  仍有 {len(self._active_requests)} 个请求未完成，强制关闭")
        
        # 清理引用
        self._active_requests.clear()
        logger.info(f"✅ HFInferenceEmbedding 实例已关闭: {self.model_name}")
    
    def __del__(self):
        """析构函数，确保资源被清理"""
        if not self._closed:
            try:
                self.close()
            except Exception:
                pass  # 析构函数中不应该抛出异常
    
    def get_llama_index_embedding(self):
        """获取LlamaIndex兼容的Embedding适配器
        
        Returns:
            LlamaIndex兼容的适配器包装器（继承自LlamaIndex BaseEmbedding）
            
        Raises:
            ImportError: 如果无法导入LlamaIndex BaseEmbedding
        """
        # 延迟导入，避免模块加载时出错
        # 优先直接导入 BaseEmbedding（而不是通过 HuggingFaceEmbedding 获取）
        LlamaBaseEmbedding = None
        try:
            from llama_index.core.embeddings.base import BaseEmbedding as LlamaBaseEmbedding
            logger.debug("✅ 成功导入 llama_index.core.embeddings.base.BaseEmbedding")
        except ImportError:
            try:
                from llama_index.embeddings.base import BaseEmbedding as LlamaBaseEmbedding
                logger.debug("✅ 成功导入 llama_index.embeddings.base.BaseEmbedding")
            except ImportError:
                # 如果直接导入失败，尝试通过 HuggingFaceEmbedding 的 MRO 找到 BaseEmbedding
                try:
                    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
                    # 通过 MRO 找到 BaseEmbedding（而不是直接取 __bases__[0]）
                    for base_class in HuggingFaceEmbedding.__mro__:
                        if base_class.__name__ == 'BaseEmbedding' and 'embeddings' in base_class.__module__:
                            LlamaBaseEmbedding = base_class
                            logger.debug(f"✅ 通过MRO找到BaseEmbedding: {base_class.__module__}.{base_class.__name__}")
                            break
                    
                    if LlamaBaseEmbedding is None:
                        raise ImportError("无法在 HuggingFaceEmbedding 的 MRO 中找到 BaseEmbedding")
                except (ImportError, AttributeError) as e:
                    # 如果都失败，抛出错误而不是返回不兼容的对象
                    error_msg = (
                        "无法导入LlamaIndex BaseEmbedding。"
                        "请确保已安装 llama-index 或 llama-index-core。"
                        f"错误详情: {e}"
                    )
                    logger.error(error_msg)
                    raise ImportError(error_msg) from e
        
        # 验证获取到的确实是 BaseEmbedding（不是 MultiModalEmbedding 或其他）
        if LlamaBaseEmbedding and LlamaBaseEmbedding.__name__ != 'BaseEmbedding':
            error_msg = (
                f"获取到的基类不是 BaseEmbedding，而是 {LlamaBaseEmbedding.__name__}。"
                f"这可能导致适配器需要实现额外的抽象方法。"
            )
            logger.warning(error_msg)
        
        # 动态创建继承LlamaBaseEmbedding的适配器类
        class LlamaIndexEmbeddingAdapter(LlamaBaseEmbedding):
            """LlamaIndex兼容的Embedding适配器包装器"""
            
            def __init__(self, embedding: HFInferenceEmbedding):
                # 先调用父类初始化（Pydantic 模型需要先初始化）
                model_name = embedding.get_model_name()
                try:
                    # 尝试使用 model_name 参数初始化
                    super().__init__(model_name=model_name)
                except (TypeError, AttributeError) as e:
                    try:
                        # 尝试无参数初始化
                        super().__init__()
                    except Exception as init_error:
                        # 如果父类初始化失败，记录警告但继续
                        logger.debug(f"父类初始化失败: {init_error}")
                        # 即使初始化失败，也继续（可能不需要参数）
                        pass
                
                # 父类初始化后再设置属性（使用 object.__setattr__ 绕过 Pydantic 验证）
                # 这样可以避免 Pydantic 的字段验证问题
                object.__setattr__(self, '_embedding', embedding)
                # model_name 可能已经在 super().__init__() 中设置了，如果没有则设置
                if not hasattr(self, 'model_name') or self.model_name != model_name:
                    try:
                        self.model_name = model_name
                    except (AttributeError, ValueError):
                        # 如果 Pydantic 不允许直接设置，使用 object.__setattr__
                        object.__setattr__(self, 'model_name', model_name)
            
            def _get_query_embedding(self, query: str) -> List[float]:
                """生成查询向量（LlamaIndex接口，私有方法，同步）"""
                return self._embedding.get_query_embedding(query)
            
            def _get_text_embedding(self, text: str) -> List[float]:
                """生成单个文本向量（LlamaIndex接口，私有方法，同步）"""
                embeddings = self._embedding.get_text_embeddings([text])
                return embeddings[0] if embeddings else []
            
            def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
                """批量生成文本向量（LlamaIndex接口，私有方法，同步）"""
                return self._embedding.get_text_embeddings(texts)
            
            async def _aget_query_embedding(self, query: str) -> List[float]:
                """生成查询向量（LlamaIndex接口，私有方法，异步）"""
                # 使用自定义线程池执行器，确保可以正确关闭
                executor = _get_or_create_executor()
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(executor, self._embedding.get_query_embedding, query)
            
            async def _aget_text_embedding(self, text: str) -> List[float]:
                """生成单个文本向量（LlamaIndex接口，私有方法，异步）"""
                # 使用自定义线程池执行器，确保可以正确关闭
                executor = _get_or_create_executor()
                loop = asyncio.get_event_loop()
                embeddings = await loop.run_in_executor(executor, self._embedding.get_text_embeddings, [text])
                return embeddings[0] if embeddings else []
            
            async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
                """批量生成文本向量（LlamaIndex接口，私有方法，异步）"""
                # 使用自定义线程池执行器，确保可以正确关闭
                executor = _get_or_create_executor()
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(executor, self._embedding.get_text_embeddings, texts)
            
            def get_query_embedding(self, query: str) -> List[float]:
                """生成查询向量（公共方法，兼容LlamaIndex接口）"""
                return self._get_query_embedding(query)
            
            def get_text_embedding(self, text: str) -> List[float]:
                """生成单个文本向量（公共方法，兼容LlamaIndex接口）"""
                return self._get_text_embedding(text)
            
            def get_text_embedding_batch(self, texts: List[str], **kwargs) -> List[List[float]]:
                """批量生成文本向量（公共方法，兼容LlamaIndex接口）
                
                Args:
                    texts: 文本列表
                    **kwargs: 额外参数（如 show_progress），会被忽略
                """
                return self._get_text_embeddings(texts)
        
        try:
            adapter = LlamaIndexEmbeddingAdapter(self)
        except TypeError as e:
            # 如果创建适配器失败（可能是抽象方法未实现），提供更详细的错误信息
            error_msg = (
                f"无法创建LlamaIndex适配器: {e}。"
                f"这可能是因为基类 {LlamaBaseEmbedding.__name__} 有未实现的抽象方法。"
                f"请检查是否需要实现额外的抽象方法。"
            )
            logger.error(error_msg)
            raise TypeError(error_msg) from e
        
        # 验证适配器确实是BaseEmbedding的实例
        if not isinstance(adapter, LlamaBaseEmbedding):
            error_msg = (
                f"创建的适配器不是LlamaIndex BaseEmbedding的实例。"
                f"类型: {type(adapter)}, 期望: {LlamaBaseEmbedding}"
            )
            logger.error(error_msg)
            raise TypeError(error_msg)
        
        logger.debug(f"✅ 成功创建LlamaIndex适配器: {type(adapter)}")
        return adapter


class _SimpleAdapter:
    """简单的适配器包装器（当无法导入LlamaIndex BaseEmbedding时使用）"""
    
    def __init__(self, embedding: HFInferenceEmbedding):
        self._embedding = embedding
        self.model_name = embedding.get_model_name()
    
    def get_query_embedding(self, query: str) -> List[float]:
        return self._embedding.get_query_embedding(query)
    
    def get_text_embedding(self, text: str) -> List[float]:
        embeddings = self._embedding.get_text_embeddings([text])
        return embeddings[0] if embeddings else []
    
    def _get_query_embedding(self, query: str) -> List[float]:
        """生成查询向量（LlamaIndex接口，私有方法）"""
        return self._embedding.get_query_embedding(query)
    
    def _get_text_embedding(self, text: str) -> List[float]:
        """生成单个文本向量（LlamaIndex接口，私有方法）"""
        embeddings = self._embedding.get_text_embeddings([text])
        return embeddings[0] if embeddings else []
    
    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本向量（LlamaIndex接口，私有方法）"""
        return self._embedding.get_text_embeddings(texts)
    
    def get_query_embedding(self, query: str) -> List[float]:
        """生成查询向量（公共方法，兼容LlamaIndex接口）"""
        return self._get_query_embedding(query)
    
    def get_text_embedding(self, text: str) -> List[float]:
        """生成单个文本向量（公共方法，兼容LlamaIndex接口）"""
        return self._get_text_embedding(text)
    
    def get_text_embedding_batch(self, texts: List[str], **kwargs) -> List[List[float]]:
        """批量生成文本向量（公共方法，兼容LlamaIndex接口）
        
        Args:
            texts: 文本列表
            **kwargs: 额外参数（如 show_progress），会被忽略
        """
        return self._get_text_embeddings(texts)
