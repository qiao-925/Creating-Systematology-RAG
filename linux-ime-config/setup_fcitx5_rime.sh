#!/bin/bash
# Fcitx5 + Rime 快速配置脚本

set -e

echo "=========================================="
echo "Fcitx5 + Rime 快速配置脚本"
echo "=========================================="
echo ""

# 检查是否以 root 运行
if [ "$EUID" -eq 0 ]; then 
   echo "请不要使用 root 用户运行此脚本"
   exit 1
fi

# 1. 安装 Fcitx5 和 Rime
echo "=========================================="
echo "步骤 1: 安装 Fcitx5 和 Rime"
echo "=========================================="

if ! command -v fcitx5 &> /dev/null; then
    echo "安装 Fcitx5 框架..."
    sudo apt update
    sudo apt install -y fcitx5 fcitx5-config-qt
else
    echo "✅ Fcitx5 已安装"
fi

if ! dpkg -l | grep -q "^ii.*fcitx5-rime"; then
    echo "安装 Rime 输入法引擎..."
    sudo apt install -y fcitx5-rime \
        librime-data-luna-pinyin \
        librime-data-stroke \
        librime-data-pinyin-simp \
        librime-data-dict
else
    echo "✅ Rime 已安装"
fi

echo ""

# 2. 配置环境变量
echo "=========================================="
echo "步骤 2: 配置环境变量"
echo "=========================================="

# 配置 ~/.xprofile
XPROFILE="$HOME/.xprofile"
if [ ! -f "$XPROFILE" ] || ! grep -q "GTK_IM_MODULE" "$XPROFILE"; then
    echo "配置 ~/.xprofile..."
    cat >> "$XPROFILE" << 'EOF'

# Fcitx5 输入法环境变量
export GTK_IM_MODULE=fcitx5
export QT_IM_MODULE=fcitx5
export XMODIFIERS=@im=fcitx5
EOF
    echo "✅ 已添加环境变量到 ~/.xprofile"
else
    echo "⚠️  ~/.xprofile 中已存在环境变量配置"
fi

# 配置 ~/.pam_environment
PAM_ENV="$HOME/.pam_environment"
if [ ! -f "$PAM_ENV" ] || ! grep -q "GTK_IM_MODULE" "$PAM_ENV"; then
    echo "配置 ~/.pam_environment..."
    cat >> "$PAM_ENV" << 'EOF'
GTK_IM_MODULE=fcitx5
QT_IM_MODULE=fcitx5
XMODIFIERS=@im=fcitx5
EOF
    echo "✅ 已添加环境变量到 ~/.pam_environment"
else
    echo "⚠️  ~/.pam_environment 中已存在环境变量配置"
fi

# 配置 ~/.bashrc（可选，用于某些应用）
BASHRC="$HOME/.bashrc"
if [ -f "$BASHRC" ] && ! grep -q "XMODIFIERS.*fcitx5" "$BASHRC"; then
    echo "配置 ~/.bashrc..."
    cat >> "$BASHRC" << 'EOF'

# Fcitx5 输入法环境变量
export GTK_IM_MODULE=fcitx5
export QT_IM_MODULE=fcitx5
export XMODIFIERS=@im=fcitx5
EOF
    echo "✅ 已添加环境变量到 ~/.bashrc"
fi

echo ""

# 3. 创建 Rime 配置目录
echo "=========================================="
echo "步骤 3: 创建 Rime 配置目录"
echo "=========================================="

RIME_DIR="$HOME/.local/share/fcitx5/rime"
mkdir -p "$RIME_DIR"
echo "✅ Rime 配置目录: $RIME_DIR"

# 4. 创建基础配置文件
echo ""
echo "=========================================="
echo "步骤 4: 创建基础配置文件"
echo "=========================================="

# 创建 default.custom.yaml
DEFAULT_CONFIG="$RIME_DIR/default.custom.yaml"
if [ ! -f "$DEFAULT_CONFIG" ]; then
    cat > "$DEFAULT_CONFIG" << 'EOF'
# default.custom.yaml
# Rime 默认配置自定义文件

patch:
  # 候选词数量（每页显示数量）
  "menu/page_size": 7
  
  # 输入法切换快捷键
  "switcher/hotkeys":
    - "Control+Shift+grave"
  
  # 字体大小（可根据需要调整）
  "style/font_point": 14
  
  # 候选词横排显示（true=横排, false=竖排）
  "style/horizontal": true
  
  # 启用内嵌编码提示
  "style/inline_preedit": true
EOF
    echo "✅ 已创建 default.custom.yaml"
else
    echo "⚠️  default.custom.yaml 已存在，跳过"
fi

# 创建 luna_pinyin.custom.yaml（拼音方案自定义）
LUNA_CONFIG="$RIME_DIR/luna_pinyin.custom.yaml"
if [ ! -f "$LUNA_CONFIG" ]; then
    cat > "$LUNA_CONFIG" << 'EOF'
# luna_pinyin.custom.yaml
# 朙月拼音方案自定义配置

patch:
  # 启用自动纠错
  "translator/enable_completion": true
  
  # 启用用户词库
  "engine/translators/@before 0": table_translator@user_dict
EOF
    echo "✅ 已创建 luna_pinyin.custom.yaml"
else
    echo "⚠️  luna_pinyin.custom.yaml 已存在，跳过"
fi

echo ""

# 5. 显示配置完成信息
echo "=========================================="
echo "✅ 基础配置完成！"
echo "=========================================="
echo ""
echo "📋 下一步操作："
echo ""
echo "1. 设置系统默认输入法框架："
echo "   系统设置 → 区域与语言 → 管理已安装的语言"
echo "   键盘输入法系统选择：Fcitx 5"
echo ""
echo "2. 重新登录系统（重要！）"
echo ""
echo "3. 配置输入法："
echo "   运行: fcitx5-config-qt"
echo "   在配置工具中："
echo "   - 点击 '+' 添加输入法"
echo "   - 取消勾选 '只显示当前语言'"
echo "   - 搜索并添加 '中州韵（Rime）'"
echo "   - 点击 '确定' 保存"
echo ""
echo "4. 部署 Rime 配置："
echo "   在 fcitx5-config-qt 中，右键 Rime 输入法"
echo "   选择 '部署'，或运行: fcitx5-rime --deploy"
echo ""
echo "5. 测试输入法："
echo "   按 Ctrl+Space 激活输入法"
echo "   输入拼音测试，如：nihao"
echo ""
echo "=========================================="
echo "📚 详细教程请查看: FCITX5_RIME_TUTORIAL.md"
echo "=========================================="
echo ""
echo "💡 提示："
echo "   - 配置文件位置: $RIME_DIR"
echo "   - 修改配置后需要重新部署才能生效"
echo "   - 使用 fcitx5-diagnose 诊断问题"
echo ""


