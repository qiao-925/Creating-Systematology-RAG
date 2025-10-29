"""简化版 GPU 测试 - 直接测试模型"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

import torch
print(f"[OK] PyTorch version: {torch.__version__}")
print(f"[OK] CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"[OK] GPU device: {torch.cuda.get_device_name(0)}")
    print(f"[OK] CUDA version: {torch.version.cuda}")

print("\n开始加载模型...")

try:
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from pathlib import Path
    
    model_name = "Qwen/Qwen3-Embedding-0.6B"
    cache_folder = str(Path.home() / ".cache" / "huggingface")
    
    # 检测 GPU
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    model = HuggingFaceEmbedding(
        model_name=model_name,
        trust_remote_code=True,
        cache_folder=cache_folder,
        model_kwargs={
            "device_map": None,
            "dtype": "float16" if device.startswith("cuda") else "float32",
        },
        embed_batch_size=10,
        max_length=512,
    )
    
    print("[OK] Model loaded successfully")
    
    # 手动将模型移到 GPU
    if device.startswith("cuda") and torch.cuda.is_available():
        if hasattr(model, 'model') and hasattr(model.model, 'to'):
            model.model = model.model.to(device)
            print(f"[OK] Model moved to GPU: {device}")
    
    # 测试生成 embedding
    print("\n测试生成 embedding...")
    test_text = "这是一个测试文本"
    import time
    start_time = time.time()
    embedding = model.get_query_embedding(test_text)
    elapsed = time.time() - start_time
    print(f"[OK] Embedding generated in {elapsed:.3f}s")
    print(f"[OK] Embedding type: {type(embedding)}, length: {len(embedding) if isinstance(embedding, list) else 'N/A'}")
    
    # 检查模型设备
    if hasattr(model, 'model'):
        for name, param in model.model.named_parameters():
            print(f"[OK] Parameter '{name}' device: {param.device}")
            break
    
    print(f"\n[OK] Test completed! Speed: {elapsed:.3f}s per embedding")
    
except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()

