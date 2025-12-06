#!/bin/bash
# 多输入法安装命令 - 可直接复制执行

echo "=========================================="
echo "开始安装多个输入法..."
echo "=========================================="
echo ""

# 更新软件包列表
echo "📦 更新软件包列表..."
sudo apt update

# 安装 Fcitx5 扩展输入法
echo ""
echo "=========================================="
echo "安装 Fcitx5 扩展输入法"
echo "=========================================="

# 五笔输入法
echo "安装五笔输入法..."
sudo apt install -y fcitx5-table-wubi98 fcitx5-table-wubi-large

# 中州韵（Rime）输入法引擎
echo "安装中州韵（Rime）输入法引擎..."
sudo apt install -y fcitx5-rime librime-data-luna-pinyin librime-data-stroke librime-data-pinyin-simp

# 安装 Fcitx4（用于搜狗拼音）
echo ""
echo "=========================================="
echo "安装 Fcitx4 框架（用于搜狗拼音）"
echo "=========================================="
sudo apt install -y fcitx fcitx-config-gtk fcitx-table-all

echo ""
echo "=========================================="
echo "✅ Fcitx5 和 Fcitx4 输入法安装完成！"
echo "=========================================="
echo ""
echo "📋 已安装的输入法："
echo ""
echo "【Fcitx5 框架】"
echo "  ✅ 拼音输入法（Pinyin）"
echo "  ✅ 五笔98输入法（Wubi98）"
echo "  ✅ 五笔大词库（Wubi-Large）"
echo "  ✅ 中州韵（Rime）- 支持多种输入方案"
echo ""
echo "【Fcitx4 框架】"
echo "  ✅ 已安装框架（用于搜狗拼音）"
echo ""
echo "=========================================="
echo "下一步操作："
echo "=========================================="
echo ""
echo "1. 配置 Fcitx5 输入法："
echo "   fcitx5-config-qt"
echo ""
echo "2. 如需安装搜狗拼音："
echo "   - 访问: https://pinyin.sogou.com/linux/"
echo "   - 下载 .deb 文件"
echo "   - 执行: sudo dpkg -i sogoupinyin_*.deb"
echo "   - 执行: sudo apt -f install"
echo "   - 运行: fcitx-config-gtk 添加搜狗拼音"
echo ""
echo "3. 重新登录系统使配置生效"
echo ""
echo "4. 使用 Ctrl+Space 切换输入法"
echo ""


