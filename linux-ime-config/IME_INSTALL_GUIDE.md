# Linux 多输入法安装指南

## 📋 当前状态

✅ **已安装：**
- Fcitx5 框架
- Fcitx5 拼音输入法
- Fcitx5 表格输入法（支持五笔等）

## 🚀 安装步骤

### 步骤 1: 安装 Fcitx5 扩展输入法

执行以下命令安装更多输入法选项：

```bash
# 安装五笔输入法（推荐安装五笔98和大词库版本）
sudo apt install -y fcitx5-table-wubi98 fcitx5-table-wubi-large

# 安装中州韵（Rime）输入法引擎
sudo apt install -y fcitx5-rime librime-data-luna-pinyin librime-data-stroke librime-data-pinyin-simp
```

### 步骤 2: 安装 Fcitx4 和搜狗拼音

```bash
# 安装 Fcitx4 框架
sudo apt install -y fcitx fcitx-config-gtk fcitx-table-all

# 下载搜狗拼音（需要手动下载）
# 访问: https://pinyin.sogou.com/linux/
# 下载后执行：
# sudo dpkg -i sogoupinyin_*.deb
# sudo apt -f install
```

### 步骤 3: 配置环境变量

环境变量已配置为使用 Fcitx5（默认）。如需切换到 Fcitx4，使用切换脚本：

```bash
# 查看当前设置
switch_ime

# 切换到 Fcitx5
switch_ime fcitx5

# 切换到 Fcitx4（搜狗拼音）
switch_ime fcitx
```

### 步骤 4: 配置输入法

**配置 Fcitx5：**
```bash
fcitx5-config-qt
```

在配置工具中添加：
- 拼音（Pinyin）- ✅ 已安装
- 五笔98（Wubi98）- 需安装 fcitx5-table-wubi98
- 五笔大词库（Wubi-Large）- 需安装 fcitx5-table-wubi-large
- 中州韵（Rime）- 需安装 fcitx5-rime

**配置 Fcitx4（搜狗拼音）：**
```bash
fcitx-config-gtk
```

在配置工具中：
1. 取消勾选"只显示当前语言"
2. 搜索并添加"Sogou Pinyin"

### 步骤 5: 设置系统默认输入法框架

1. 打开"系统设置" → "区域与语言" → "管理已安装的语言"
2. 在"键盘输入法系统"中选择：
   - **Fcitx5** - 使用拼音、五笔、Rime
   - **Fcitx** - 使用搜狗拼音

### 步骤 6: 重新登录

重新登录系统使配置生效。

## 🎯 使用说明

### 快捷键
- `Ctrl + Space`: 切换中英文
- `Ctrl + Shift`: 切换不同输入法
- `Shift`: 临时切换中英文（部分输入法）

### 查看输入法状态
```bash
# Fcitx5 诊断
fcitx5-diagnose

# Fcitx4 诊断
fcitx-diagnose
```

### 已安装的输入法列表

**Fcitx5 框架：**
- ✅ 拼音输入法（Pinyin）- 已安装
- ⏳ 五笔98输入法（Wubi98）- 执行安装脚本后可用
- ⏳ 五笔大词库（Wubi-Large）- 执行安装脚本后可用
- ⏳ 中州韵（Rime）- 执行安装脚本后可用

**Fcitx4 框架：**
- ✅ 框架已安装 - 执行安装脚本后可用
- ⏳ 搜狗拼音 - 需从官网下载安装

## 🔧 快速安装命令

**方式一：使用安装脚本（推荐）**
```bash
./install_ime_commands.sh
```

**方式二：手动执行命令**
```bash
# 一键安装所有 Fcitx5 输入法
sudo apt update && \
sudo apt install -y \
  fcitx5-table-wubi98 \
  fcitx5-table-wubi-large \
  fcitx5-rime \
  librime-data-luna-pinyin \
  librime-data-stroke \
  librime-data-pinyin-simp \
  fcitx \
  fcitx-config-gtk \
  fcitx-table-all
```

## 📝 注意事项

1. **框架切换**：Fcitx5 和 Fcitx4 可以共存，但需要手动切换默认框架
2. **环境变量**：切换框架后需要重新登录才能生效
3. **搜狗拼音**：需要从官网下载 .deb 包手动安装
4. **Wayland 支持**：Fcitx5 对 Wayland 支持更好

## 🐛 故障排查

**输入法无法启动：**
```bash
# 检查环境变量
echo $GTK_IM_MODULE
echo $QT_IM_MODULE
echo $XMODIFIERS

# 查看日志
journalctl -u fcitx5 --since "1 hour ago"
```

**应用内无法输入中文：**
- 确保环境变量已设置
- 重启相关应用
- 检查应用是否支持输入法框架

**性能问题：**
- 减少同时启用的输入法数量
- 使用 Fcitx5 替代 Fcitx4（性能更好）

