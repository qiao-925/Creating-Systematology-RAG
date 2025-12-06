#!/bin/bash
# 多输入法安装脚本 - 安装搜狗拼音、Fcitx5 中文输入法等

set -e

echo "=========================================="
echo "多输入法安装脚本"
echo "=========================================="
echo ""

# 检查系统架构
ARCH=$(dpkg --print-architecture)
echo "检测到系统架构: $ARCH"
echo ""

# 1. 安装 Fcitx5 中文输入法扩展
echo "=========================================="
echo "步骤 1: 安装 Fcitx5 中文输入法扩展"
echo "=========================================="

# 检查 Fcitx5 是否已安装
if ! command -v fcitx5 &> /dev/null; then
    echo "安装 Fcitx5..."
    sudo apt update
    sudo apt install -y fcitx5 fcitx5-chinese-addons fcitx5-config-qt
else
    echo "✅ Fcitx5 已安装"
fi

# 安装 Fcitx5 的拼音输入法
echo "安装 Fcitx5 拼音输入法..."
sudo apt install -y fcitx5-pinyin

# 安装 Fcitx5 五笔输入法
echo "安装 Fcitx5 五笔输入法..."
sudo apt install -y fcitx5-table fcitx5-table-wubi

# 安装中州韵（Rime）输入法引擎
echo "安装中州韵（Rime）输入法引擎..."
sudo apt install -y fcitx5-rime librime-data-luna-pinyin librime-data-stroke

echo "✅ Fcitx5 中文输入法扩展安装完成"
echo ""

# 2. 安装 Fcitx4（用于搜狗拼音）
echo "=========================================="
echo "步骤 2: 安装 Fcitx4 框架（用于搜狗拼音）"
echo "=========================================="

if ! dpkg -l | grep -q "^ii.*fcitx[^-]"; then
    echo "安装 Fcitx4..."
    sudo apt install -y fcitx fcitx-config-gtk fcitx-table-all
    echo "✅ Fcitx4 安装完成"
else
    echo "✅ Fcitx4 已安装"
fi
echo ""

# 3. 下载并安装搜狗拼音
echo "=========================================="
echo "步骤 3: 安装搜狗拼音输入法"
echo "=========================================="

if dpkg -l | grep -q "^ii.*sogoupinyin"; then
    echo "✅ 搜狗拼音已安装"
else
    DOWNLOAD_DIR="$HOME/Downloads"
    SOGOU_DEB=""
    
    # 尝试在 Downloads 目录查找
    if [ -d "$DOWNLOAD_DIR" ]; then
        SOGOU_DEB=$(find "$DOWNLOAD_DIR" -name "sogoupinyin*.deb" -type f 2>/dev/null | head -1)
    fi
    
    if [ -n "$SOGOU_DEB" ] && [ -f "$SOGOU_DEB" ]; then
        echo "找到搜狗拼音安装包: $SOGOU_DEB"
        echo "正在安装..."
        sudo dpkg -i "$SOGOU_DEB" || sudo apt -f install -y
        echo "✅ 搜狗拼音安装完成"
    else
        echo "⚠️  未找到搜狗拼音安装包"
        echo "请访问以下网址下载："
        echo "   https://pinyin.sogou.com/linux/"
        echo ""
        echo "下载后，将 .deb 文件放到 ~/Downloads 目录，然后重新运行此脚本"
        echo "或者手动安装："
        echo "   sudo dpkg -i sogoupinyin_*.deb"
        echo "   sudo apt -f install"
    fi
fi
echo ""

# 4. 配置环境变量（同时支持 Fcitx4 和 Fcitx5）
echo "=========================================="
echo "步骤 4: 配置环境变量"
echo "=========================================="

# 配置 ~/.xprofile（优先使用 Fcitx5，可通过设置切换）
XPROFILE="$HOME/.xprofile"
if [ ! -f "$XPROFILE" ] || ! grep -q "GTK_IM_MODULE" "$XPROFILE"; then
    echo "配置 ~/.xprofile..."
    cat >> "$XPROFILE" << 'EOF'

# 输入法环境变量（默认使用 Fcitx5，如需使用 Fcitx4 请改为 fcitx）
export GTK_IM_MODULE=fcitx5
export QT_IM_MODULE=fcitx5
export XMODIFIERS=@im=fcitx5
EOF
    echo "✅ 已添加环境变量到 ~/.xprofile（默认 Fcitx5）"
else
    echo "⚠️  环境变量已存在，如需修改请手动编辑 ~/.xprofile"
    echo "   当前设置："
    grep -E "(GTK_IM_MODULE|QT_IM_MODULE|XMODIFIERS)" "$XPROFILE" 2>/dev/null || echo "   未找到相关配置"
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
    echo "⚠️  环境变量已存在，跳过"
fi
echo ""

# 5. 创建输入法切换脚本
echo "=========================================="
echo "步骤 5: 创建输入法切换工具"
echo "=========================================="

SWITCH_SCRIPT="$HOME/.local/bin/switch_ime"
mkdir -p "$HOME/.local/bin"

cat > "$SWITCH_SCRIPT" << 'EOF'
#!/bin/bash
# 输入法框架切换脚本

case "$1" in
    fcitx5|5)
        echo "切换到 Fcitx5..."
        sed -i 's/GTK_IM_MODULE=fcitx[^5]*/GTK_IM_MODULE=fcitx5/g' ~/.xprofile 2>/dev/null
        sed -i 's/QT_IM_MODULE=fcitx[^5]*/QT_IM_MODULE=fcitx5/g' ~/.xprofile 2>/dev/null
        sed -i 's/XMODIFIERS=@im=fcitx[^5]*/XMODIFIERS=@im=fcitx5/g' ~/.xprofile 2>/dev/null
        sed -i 's/GTK_IM_MODULE=fcitx[^5]*/GTK_IM_MODULE=fcitx5/g' ~/.pam_environment 2>/dev/null
        sed -i 's/QT_IM_MODULE=fcitx[^5]*/QT_IM_MODULE=fcitx5/g' ~/.pam_environment 2>/dev/null
        sed -i 's/XMODIFIERS=@im=fcitx[^5]*/XMODIFIERS=@im=fcitx5/g' ~/.pam_environment 2>/dev/null
        echo "✅ 已切换到 Fcitx5，请重新登录使配置生效"
        ;;
    fcitx|4)
        echo "切换到 Fcitx4（搜狗拼音）..."
        sed -i 's/GTK_IM_MODULE=fcitx5/GTK_IM_MODULE=fcitx/g' ~/.xprofile 2>/dev/null
        sed -i 's/QT_IM_MODULE=fcitx5/QT_IM_MODULE=fcitx/g' ~/.xprofile 2>/dev/null
        sed -i 's/XMODIFIERS=@im=fcitx5/XMODIFIERS=@im=fcitx/g' ~/.xprofile 2>/dev/null
        sed -i 's/GTK_IM_MODULE=fcitx5/GTK_IM_MODULE=fcitx/g' ~/.pam_environment 2>/dev/null
        sed -i 's/QT_IM_MODULE=fcitx5/QT_IM_MODULE=fcitx/g' ~/.pam_environment 2>/dev/null
        sed -i 's/XMODIFIERS=@im=fcitx5/XMODIFIERS=@im=fcitx/g' ~/.pam_environment 2>/dev/null
        echo "✅ 已切换到 Fcitx4，请重新登录使配置生效"
        ;;
    *)
        echo "用法: switch_ime [fcitx5|fcitx|5|4]"
        echo ""
        echo "当前设置："
        grep -E "(GTK_IM_MODULE|QT_IM_MODULE|XMODIFIERS)" ~/.xprofile 2>/dev/null | head -3
        ;;
esac
EOF

chmod +x "$SWITCH_SCRIPT"
echo "✅ 已创建切换脚本: $SWITCH_SCRIPT"
echo "   使用方法: switch_ime fcitx5 或 switch_ime fcitx"
echo ""

# 6. 生成使用说明
echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "📋 已安装的输入法："
echo ""
echo "【Fcitx5 框架】"
echo "  ✅ 拼音输入法（Pinyin）"
echo "  ✅ 五笔输入法（Wubi）"
echo "  ✅ 中州韵（Rime）- 支持多种输入方案"
echo ""
if dpkg -l | grep -q "^ii.*sogoupinyin"; then
    echo "【Fcitx4 框架】"
    echo "  ✅ 搜狗拼音输入法"
    echo ""
fi
echo "=========================================="
echo "使用说明"
echo "=========================================="
echo ""
echo "1. 重新登录系统（或重启）使配置生效"
echo ""
echo "2. 配置 Fcitx5 输入法："
echo "   运行: fcitx5-config-qt"
echo "   在配置工具中添加需要的输入法："
echo "   - 拼音（Pinyin）"
echo "   - 五笔（Wubi）"
echo "   - 中州韵（Rime）"
echo ""
if dpkg -l | grep -q "^ii.*sogoupinyin"; then
    echo "3. 配置 Fcitx4（搜狗拼音）："
    echo "   运行: fcitx-config-gtk"
    echo "   添加 'Sogou Pinyin' 输入法"
    echo ""
    echo "4. 切换输入法框架："
    echo "   使用 Fcitx5: switch_ime fcitx5"
    echo "   使用 Fcitx4: switch_ime fcitx"
    echo "   切换后需要重新登录"
    echo ""
fi
echo "5. 切换输入法快捷键："
echo "   - Ctrl+Space: 切换中英文"
echo "   - Ctrl+Shift: 切换不同输入法"
echo ""
echo "6. 查看当前输入法状态："
echo "   fcitx5-diagnose  # Fcitx5 诊断"
echo "   fcitx-diagnose   # Fcitx4 诊断"
echo ""
echo "7. 系统设置中切换默认框架："
echo "   系统设置 → 区域与语言 → 管理已安装的语言"
echo "   键盘输入法系统选择："
echo "   - Fcitx5（使用拼音、五笔、Rime）"
echo "   - Fcitx（使用搜狗拼音）"
echo ""


