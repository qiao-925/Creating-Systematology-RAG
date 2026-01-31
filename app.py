"""
Streamlit Web应用 - 单页应用入口
已重构为单页应用，所有功能通过弹窗实现，不再使用多页面架构
"""

import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入主入口
from frontend.main import main

# 调用主函数
if __name__ == "__main__":
    main()
