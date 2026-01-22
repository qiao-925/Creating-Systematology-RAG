"""
Hugging Face Inference API 客户端

主要功能：
- 处理单个和批量 API 请求
- 重试机制和错误处理
"""

import time
import json
from typing import List, Set

import requests
from requests.exceptions import RequestException

from backend.infrastructure.logger import get_logger
from backend.infrastructure.embeddings.hf_utils import TimeMonitor
from backend.infrastructure.embeddings.hf_thread_pool import _get_or_create_executor

logger = get_logger('hf_api_client')


class HFAPIClient:
    """Hugging Face Inference API 客户端"""
    
    def __init__(
        self,
        api_url: str,
        headers: dict,
        model_name: str,
        closed: bool,
        active_requests: Set[int]
    ):
        """初始化 API 客户端
        
        Args:
            api_url: API URL
            headers: 请求头
            model_name: 模型名称
            closed: 是否已关闭
            active_requests: 活跃请求集合
        """
        self.api_url = api_url
        self.headers = headers
        self.model_name = model_name
        self._closed = closed
        self._active_requests = active_requests
    
    def make_single_request(self, text: str, retry_count: int = 0) -> List[float]:
        """发起单个文本的 API 请求（带重试机制）
        
        Args:
            text: 单个文本
            retry_count: 当前重试次数
            
        Returns:
            单个向量
            
        Raises:
            RuntimeError: API 调用失败或实例已关闭
        """
        if self._closed:
            raise RuntimeError("HFInferenceEmbedding 实例已关闭，请求被取消")
        
        max_retries = 3
        payload = {"inputs": text}
        
        request_start = time.time()
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            request_elapsed = time.time() - request_start
            
            result = response.json()
            
            # 处理响应格式
            if isinstance(result, list):
                embedding = [float(x) for x in result]
            elif isinstance(result, dict):
                if "embeddings" in result:
                    embedding = [float(x) for x in result["embeddings"]]
                elif "output" in result:
                    embedding = [float(x) for x in result["output"]]
                else:
                    first_key = next(iter(result.values()))
                    embedding = [float(x) for x in first_key] if isinstance(first_key, list) else [float(first_key)]
            else:
                embedding = [float(result)] if not isinstance(result, list) else [float(x) for x in result]
            
            logger.debug(f"📡 HF API: 耗时={request_elapsed:.2f}s, 维度={len(embedding)}")
            return embedding
            
        except (RequestException, json.JSONDecodeError) as e:
            if self._closed:
                raise RuntimeError("HFInferenceEmbedding 实例已关闭，请求被取消") from e
            
            if retry_count < max_retries:
                wait_time = (retry_count + 1) * 1.0
                logger.warning(f"⚠️  请求失败，{wait_time:.1f}秒后重试 ({retry_count + 1}/{max_retries})")
                time.sleep(wait_time)
                return self.make_single_request(text, retry_count + 1)
            else:
                error_details = str(e)
                if isinstance(e, RequestException) and hasattr(e, 'response') and e.response is not None:
                    error_details = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                raise RuntimeError(f"HF API 调用失败（已重试 {max_retries} 次）: {error_details}") from e
    
    def make_request(self, texts: List[str]) -> List[List[float]]:
        """发起 API 请求（并行处理优化）
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
            
        Raises:
            RuntimeError: API 调用失败或实例已关闭
        """
        if self._closed:
            raise RuntimeError(f"HFInferenceEmbedding 实例已关闭，无法继续请求")
        
        if not texts:
            return []
        
        total = len(texts)
        logger.debug(f"📤 HF Inference API 请求: 模型={self.model_name}, 文本数量={total}")
        
        request_id = id(texts)
        self._active_requests.add(request_id)
        
        try:
            # 单个文本直接处理，无需并行
            if total == 1:
                result = self.make_single_request(texts[0])
                return [result]
            
            # 多个文本使用并行处理
            batch_start = time.time()
            time_monitor = TimeMonitor(
                logger,
                f"⏱️  HF API 并行调用: 已花费 {{elapsed}} 秒 (模型={self.model_name}, 文本数量={total})"
            )
            time_monitor.__enter__()
            
            try:
                executor = _get_or_create_executor()
                max_workers = min(5, total)  # 最多 5 个并发
                
                results = []
                errors = []
                
                # 分批并行处理
                for batch_start_idx in range(0, total, max_workers):
                    batch_end_idx = min(batch_start_idx + max_workers, total)
                    batch_texts = texts[batch_start_idx:batch_end_idx]
                    
                    futures = [executor.submit(self.make_single_request, text) for text in batch_texts]
                    
                    for i, future in enumerate(futures):
                        try:
                            result = future.result(timeout=60)
                            results.append(result)
                        except Exception as e:
                            logger.error(f"❌ 并行请求失败 (索引 {batch_start_idx + i}): {e}")
                            errors.append((batch_start_idx + i, e))
                            results.append(None)
                    
                    if batch_end_idx < total:
                        logger.debug(f"   进度: {batch_end_idx}/{total}")
                
                # 检查是否有失败
                if errors:
                    failed_count = len(errors)
                    logger.warning(f"⚠️  {failed_count}/{total} 个请求失败")
                    for idx, error in errors:
                        try:
                            logger.debug(f"   重试索引 {idx}...")
                            results[idx] = self.make_single_request(texts[idx])
                        except Exception as retry_error:
                            logger.error(f"❌ 重试失败 (索引 {idx}): {retry_error}")
                            raise RuntimeError(f"批量请求失败，索引 {idx}: {retry_error}") from retry_error
                
                batch_elapsed = time.time() - batch_start
                avg_time = batch_elapsed / total
                logger.info(
                    f"📥 并行批量完成: {total} 个文本, "
                    f"总耗时={batch_elapsed:.2f}s, 平均={avg_time:.2f}s/个"
                )
                
                return results
                
            finally:
                time_monitor.__exit__(None, None, None)
        finally:
            self._active_requests.discard(request_id)
