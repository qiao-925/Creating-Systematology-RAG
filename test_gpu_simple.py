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
        # HuggingFaceEmbedding 使用 _model 属性
        if hasattr(model, '_model') and hasattr(model._model, 'to'):
            model._model = model._model.to(device)
            print(f"[OK] Model moved to GPU: {device}")
        elif hasattr(model, 'model') and hasattr(model.model, 'to'):
            model.model = model.model.to(device)
            print(f"[OK] Model moved to GPU: {device}")
        else:
            print(f"[WARNING] Cannot move model to GPU: no model attribute found")
    
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
    print("\n检查模型设备...")
    
    # 检查 _model 属性
    if hasattr(model, '_model'):
        internal_model = model._model
        print(f"_model type: {type(internal_model)}")
        
        if hasattr(internal_model, 'named_parameters'):
            params_on_cuda = 0
            params_on_cpu = 0
            param_count = 0
            for name, param in internal_model.named_parameters():
                param_count += 1
                device_str = str(param.device)
                if 'cuda' in device_str:
                    params_on_cuda += 1
                else:
                    params_on_cpu += 1
                if param_count <= 5:
                    print(f"  {name}: {device_str}")
            
            print(f"\n参数统计: {params_on_cuda} 个在 GPU, {params_on_cpu} 个在 CPU")
            
            if params_on_cuda > 0:
                print("[OK] 模型正在使用 GPU!")
            elif params_on_cpu > 0:
                print("[WARNING] 模型未使用 GPU - 所有参数在 CPU")
            else:
                print("[WARNING] 无法检查模型参数")
        else:
            print("[WARNING] _model 没有 named_parameters 方法")
    else:
        print("[WARNING] _model 属性不存在")
        print(f"Available attributes: {[attr for attr in dir(model) if not attr.startswith('__')]}")
    
    print(f"\n[OK] Test completed! Speed: {elapsed:.3f}s per embedding")
    
except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()

