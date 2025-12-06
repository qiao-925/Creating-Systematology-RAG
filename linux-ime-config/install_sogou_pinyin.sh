#!/bin/bash
# 搜狗拼音输入法安装脚本
# 注意：搜狗拼音主要支持 Fcitx4，当前系统已安装 Fcitx5

set -e

echo "=========================================="
echo "搜狗拼音输入法安装脚本"
echo "=========================================="
echo ""

# 检查系统架构
ARCH=$(dpkg --print-architecture)
echo "检测到系统架构: $ARCH"

# 检查是否已安装搜狗拼音
if dpkg -l | grep -q "^ii.*sogoupinyin"; then
    echo "⚠️  搜狗拼音已安装，跳过安装步骤"
else
    echo "📦 开始安装搜狗拼音输入法..."
    
    # 1. 安装 Fcitx（Fcitx4，搜狗拼音需要）
    echo ""
    echo "步骤 1: 安装 Fcitx 输入法框架..."
    sudo apt update
    sudo apt install -y fcitx fcitx-config-gtk fcitx-table-all
    
    # 2. 下载搜狗拼音（如果未下载）
    SOGOU_URL="https://pinyin.sogou.com/linux/download.php?f=linux&bit=64"
    DOWNLOAD_DIR="$HOME/Downloads"
    SOGOU_DEB=""
    
    echo ""
    echo "步骤 2: 下载搜狗拼音输入法..."
    echo "请访问以下网址下载最新版本："
    echo "https://pinyin.sogou.com/linux/"
    echo ""
    read -p "请输入下载的 .deb 文件完整路径（或按 Enter 使用默认 ~/Downloads 目录下的文件）: " SOGOU_DEB
    
    if [ -z "$SOGOU_DEB" ]; then
        # 尝试在 Downloads 目录查找
        SOGOU_DEB=$(find "$DOWNLOAD_DIR" -name "sogoupinyin*.deb" -type f | head -1)
        if [ -z "$SOGOU_DEB" ]; then
            echo "❌ 未找到搜狗拼音安装包，请先下载："
            echo "   https://pinyin.sogou.com/linux/"
            exit 1
        fi
    fi
    
    if [ ! -f "$SOGOU_DEB" ]; then
        echo "❌ 文件不存在: $SOGOU_DEB"
        exit 1
    fi
    
    echo "找到安装包: $SOGOU_DEB"
    
    # 3. 安装搜狗拼音
    echo ""
    echo "步骤 3: 安装搜狗拼音..."
    sudo dpkg -i "$SOGOU_DEB" || sudo apt -f install -y
    
    echo "✅ 搜狗拼音安装完成"
fi

# 4. 配置环境变量
echo ""
echo "步骤 4: 配置环境变量..."

# 检查并配置 ~/.xprofile
XPROFILE="$HOME/.xprofile"
if [ ! -f "$XPROFILE" ] || ! grep -q "XMODIFIERS" "$XPROFILE"; then
    echo "配置 ~/.xprofile..."
    cat >> "$XPROFILE" << 'EOF'

# Fcitx 输入法环境变量
export GTK_IM_MODULE=fcitx
export QT_IM_MODULE=fcitx
export XMODIFIERS=@im=fcitx
EOF
    echo "✅ 已添加环境变量到 ~/.xprofile"
else
    echo "⚠️  环境变量已存在，跳过"
fi

# 5. 配置 ~/.pam_environment（用于登录时加载）
PAM_ENV="$HOME/.pam_environment"
if [ ! -f "$PAM_ENV" ] || ! grep -q "XMODIFIERS" "$PAM_ENV"; then
    echo "配置 ~/.pam_environment..."
    cat >> "$PAM_ENV" << 'EOF'
GTK_IM_MODULE=fcitx
QT_IM_MODULE=fcitx
XMODIFIERS=@im=fcitx
EOF
    echo "✅ 已添加环境变量到 ~/.pam_environment"
else
    echo "⚠️  环境变量已存在，跳过"
fi

# 6. 设置默认输入法框架
echo ""
echo "步骤 5: 设置输入法框架..."
echo "⚠️  重要提示："
echo "   1. 搜狗拼音需要 Fcitx（Fcitx4），而您的系统已安装 Fcitx5"
echo "   2. 两者可以共存，但需要手动切换"
echo ""
echo "请执行以下操作："
echo "   1. 打开 '系统设置' → '区域与语言' → '管理已安装的语言'"
echo "   2. 在 '键盘输入法系统' 中选择 'Fcitx'（不是 Fcitx5）"
echo "   3. 点击 '应用到整个系统'"
echo ""
echo "或者运行以下命令（需要图形界面）："
echo "   im-config -n fcitx"
echo ""

# 7. 启动 Fcitx 配置工具
echo ""
echo "步骤 6: 配置输入法..."
echo "安装完成后，请运行以下命令打开配置工具："
echo "   fcitx-config-gtk"
echo ""
echo "在配置工具中："
echo "   1. 点击 '+' 添加输入法"
echo "   2. 取消勾选 '只显示当前语言'"
echo "   3. 搜索并添加 'Sogou Pinyin'"
echo "   4. 点击 '确定' 保存"
echo ""

echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo "1. 重新登录系统（或重启）使配置生效"
echo "2. 使用 Ctrl+Space 切换输入法"
echo "3. 如果遇到问题，运行: fcitx-diagnose"
echo ""


