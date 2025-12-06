# Fcitx5 + 中州韵（Rime）完整配置教程

## 📋 目录

1. [安装步骤](#1-安装步骤)
2. [环境变量配置](#2-环境变量配置)
3. [系统设置](#3-系统设置)
4. [Rime 配置](#4-rime-配置)
5. [输入方案选择](#5-输入方案选择)
6. [高级定制](#6-高级定制)
7. [常见问题](#7-常见问题)

---

## 1. 安装步骤

### 1.1 安装 Fcitx5 和 Rime

```bash
# 更新软件包列表
sudo apt update

# 安装 Fcitx5 框架
sudo apt install -y fcitx5 fcitx5-config-qt

# 安装 Rime 输入法引擎
sudo apt install -y fcitx5-rime

# 安装 Rime 输入方案数据包
sudo apt install -y \
  librime-data-luna-pinyin \
  librime-data-stroke \
  librime-data-pinyin-simp \
  librime-data-dict \
  librime-data-combo-pinyin
```

### 1.2 验证安装

```bash
# 检查 Fcitx5 是否安装成功
fcitx5 --version

# 检查 Rime 是否安装成功
fcitx5-rime --version
```

---

## 2. 环境变量配置

### 2.1 配置 ~/.xprofile（X11 环境）

```bash
# 编辑或创建 ~/.xprofile
nano ~/.xprofile
```

添加以下内容：

```bash
# Fcitx5 输入法环境变量
export GTK_IM_MODULE=fcitx5
export QT_IM_MODULE=fcitx5
export XMODIFIERS=@im=fcitx5
```

### 2.2 配置 ~/.pam_environment（登录时加载）

```bash
# 编辑或创建 ~/.pam_environment
nano ~/.pam_environment
```

添加以下内容：

```
GTK_IM_MODULE=fcitx5
QT_IM_MODULE=fcitx5
XMODIFIERS=@im=fcitx5
```

### 2.3 配置 ~/.bashrc 或 ~/.zshrc（可选）

如果某些应用无法识别环境变量，可以在 shell 配置文件中添加：

```bash
# 编辑 ~/.bashrc 或 ~/.zshrc
nano ~/.bashrc
```

添加：

```bash
# Fcitx5 输入法环境变量
export GTK_IM_MODULE=fcitx5
export QT_IM_MODULE=fcitx5
export XMODIFIERS=@im=fcitx5
```

然后重新加载配置：

```bash
source ~/.bashrc
```

---

## 3. 系统设置

### 3.1 设置默认输入法框架

**方法一：图形界面设置**

1. 打开"系统设置"（Settings）
2. 进入"区域与语言"（Region & Language）
3. 点击"管理已安装的语言"（Manage Installed Languages）
4. 在"键盘输入法系统"（Keyboard input method system）中选择 **Fcitx 5**
5. 点击"应用到整个系统"（Apply System-Wide）
6. 关闭窗口

**方法二：命令行设置**

```bash
# 使用 im-config（如果可用）
im-config -n fcitx5
```

### 3.2 重新登录

**重要：** 配置完成后必须重新登录系统才能使配置生效。

```bash
# 或者重启系统
sudo reboot
```

---

## 4. Rime 配置

### 4.1 打开 Fcitx5 配置工具

```bash
fcitx5-config-qt
```

### 4.2 添加 Rime 输入法

1. 在配置工具中，点击"输入法"（Input Method）标签
2. 点击左下角的"+"按钮
3. 取消勾选"只显示当前语言"（Only show current language）
4. 在搜索框中输入"rime"或"中州韵"
5. 选择"中州韵（Rime）"或"Rime"
6. 点击"确定"（OK）添加

### 4.3 调整输入法顺序

在输入法列表中，可以：
- 使用上下箭头调整顺序
- 使用"-"按钮移除不需要的输入法
- 设置默认输入法（第一个）

### 4.4 配置快捷键

1. 在配置工具中，点击"全局选项"（Global Options）标签
2. 可以设置：
   - **切换激活状态**：默认 `Ctrl+Space`（切换中英文）
   - **切换输入法**：默认 `Ctrl+Shift`（切换不同输入法）
   - **上一页/下一页**：翻页快捷键

---

## 5. 输入方案选择

### 5.1 切换输入方案

Rime 支持多种输入方案，切换方法：

1. 按 `Ctrl+Space` 激活输入法
2. 按 `F4` 或点击输入法状态栏中的方案名称
3. 选择需要的输入方案

### 5.2 常用输入方案

**拼音方案：**
- **朙月拼音**（luna_pinyin）：默认拼音方案，简洁高效
- **简体拼音**（pinyin_simp）：简体中文优化
- **双拼**（double_pinyin）：双拼输入，速度快

**其他方案：**
- **五笔**（wubi）：五笔输入法
- **笔画**（stroke）：笔画输入
- **注音**（bopomofo）：注音输入

### 5.3 安装更多输入方案

```bash
# 安装更多 Rime 数据包
sudo apt install -y \
  librime-data-wubi \
  librime-data-double-pinyin \
  librime-data-bopomofo
```

---

## 6. 高级定制

### 6.1 Rime 配置目录

Rime 的配置文件位于：

```bash
~/.local/share/fcitx5/rime/
```

或：

```bash
~/.config/fcitx/rime/
```

### 6.2 自定义配置

#### 6.2.1 创建用户配置目录

```bash
# 创建配置目录
mkdir -p ~/.local/share/fcitx5/rime/

# 进入配置目录
cd ~/.local/share/fcitx5/rime/
```

#### 6.2.2 创建默认配置文件

创建 `default.custom.yaml`：

```bash
nano ~/.local/share/fcitx5/rime/default.custom.yaml
```

内容示例：

```yaml
# default.custom.yaml
patch:
  # 候选词数量
  "menu/page_size": 7
  
  # 输入法切换快捷键
  "switcher/hotkeys":
    - "Control+Shift+grave"
  
  # 字体大小
  "style/font_point": 14
  
  # 候选词横排显示
  "style/horizontal": true
```

#### 6.2.3 自定义拼音方案

创建 `luna_pinyin.custom.yaml`：

```bash
nano ~/.local/share/fcitx5/rime/luna_pinyin.custom.yaml
```

内容示例：

```yaml
# luna_pinyin.custom.yaml
patch:
  # 启用简繁转换
  "translator/enable_completion": true
  
  # 自定义词库路径
  "translator/dictionary": luna_pinyin
  
  # 启用用户词库
  "engine/translators/@before 0": table_translator@user_dict
```

#### 6.2.4 用户词库

创建用户词库文件 `luna_pinyin.userdb/`：

```bash
# 用户词库会自动创建，也可以手动编辑
# 格式：词条 + Tab + 编码 + Tab + 权重
```

### 6.3 部署配置

修改配置后，需要重新部署 Rime：

**方法一：通过 Fcitx5 配置工具**
1. 打开 `fcitx5-config-qt`
2. 在 Rime 输入法上右键
3. 选择"部署"（Deploy）

**方法二：命令行部署**

```bash
# 使用 fcitx5-rime 部署
fcitx5-rime --deploy

# 或者重启 Fcitx5
killall fcitx5
fcitx5 -d
```

### 6.4 常用自定义配置示例

#### 示例 1：调整候选词数量

```yaml
# default.custom.yaml
patch:
  "menu/page_size": 9  # 每页显示 9 个候选词
```

#### 示例 2：启用模糊音

```yaml
# luna_pinyin.custom.yaml
patch:
  "speller/algebra":
    - xform/^([zcs])h/$1/  # zh -> z
    - xform/^([zcs])([^h])/$1h$2/  # z -> zh
```

#### 示例 3：自定义标点符号

```yaml
# default.custom.yaml
patch:
  "punctuator/full_shape":
    "，" : "，"
    "。" : "。"
    "？" : "？"
    "！" : "！"
```

---

## 7. 常见问题

### 7.1 输入法无法启动

**问题：** 按 `Ctrl+Space` 没有反应

**解决方案：**

```bash
# 1. 检查环境变量
echo $GTK_IM_MODULE
echo $QT_IM_MODULE
echo $XMODIFIERS

# 2. 检查 Fcitx5 是否运行
ps aux | grep fcitx5

# 3. 手动启动 Fcitx5
fcitx5 -d

# 4. 查看诊断信息
fcitx5-diagnose
```

### 7.2 应用内无法输入中文

**问题：** 某些应用（如 VSCode、JetBrains IDE）无法输入中文

**解决方案：**

```bash
# 1. 确保环境变量已设置
export GTK_IM_MODULE=fcitx5
export QT_IM_MODULE=fcitx5
export XMODIFIERS=@im=fcitx5

# 2. 重启应用
# 3. 检查应用启动脚本，确保加载环境变量
```

**VSCode 特殊配置：**

在 `~/.vscode/argv.json` 中添加：

```json
{
  "enable-proposed-api": []
}
```

或在启动脚本中添加环境变量。

### 7.3 Rime 配置不生效

**问题：** 修改配置文件后没有效果

**解决方案：**

```bash
# 1. 检查配置文件语法
# YAML 文件对缩进敏感，必须使用空格，不能使用 Tab

# 2. 重新部署
fcitx5-rime --deploy

# 3. 重启 Fcitx5
killall fcitx5
fcitx5 -d

# 4. 检查配置文件位置
ls -la ~/.local/share/fcitx5/rime/
```

### 7.4 候选词显示异常

**问题：** 候选词显示乱码或格式异常

**解决方案：**

```bash
# 1. 检查字体支持
fc-list | grep -i "sans\|serif"

# 2. 在配置中指定字体
# default.custom.yaml
patch:
  "style/font_face": "Noto Sans CJK SC"
```

### 7.5 输入法切换快捷键冲突

**问题：** 快捷键与其他应用冲突

**解决方案：**

1. 打开 `fcitx5-config-qt`
2. 进入"全局选项"标签
3. 修改快捷键设置
4. 避免使用系统级快捷键（如 `Super` 键组合）

### 7.6 Wayland 环境问题

**问题：** 在 Wayland 下输入法不工作

**解决方案：**

```bash
# 1. 确保使用 Fcitx5（Fcitx4 对 Wayland 支持不佳）

# 2. 安装 Wayland 支持
sudo apt install -y fcitx5-module-wayland

# 3. 检查环境变量
export WAYLAND_IM_MODULE=fcitx5
```

---

## 8. 实用技巧

### 8.1 快速切换输入方案

- `F4`：打开方案选择菜单
- `Ctrl+Shift+grave`：快速切换（如果已配置）

### 8.2 用户词库管理

```bash
# 查看用户词库
ls ~/.local/share/fcitx5/rime/*.userdb/

# 备份用户词库
cp -r ~/.local/share/fcitx5/rime/*.userdb/ ~/rime_backup/
```

### 8.3 导入词库

Rime 支持导入外部词库：

1. 准备词库文件（格式：词条 + Tab + 编码）
2. 放置到配置目录
3. 在方案配置中引用
4. 重新部署

### 8.4 同步配置（多设备）

```bash
# 备份配置
tar -czf rime_config_backup.tar.gz ~/.local/share/fcitx5/rime/

# 恢复配置
tar -xzf rime_config_backup.tar.gz -C ~/.local/share/fcitx5/rime/
```

---

## 9. 参考资源

- **Fcitx5 官网**：https://fcitx-im.org/
- **Rime 官网**：https://rime.im/
- **Rime 配置指南**：https://github.com/rime/home/wiki
- **Rime 输入方案**：https://github.com/rime/plum

---

## 10. 快速检查清单

安装配置完成后，使用以下命令检查：

```bash
# 1. 检查 Fcitx5 是否运行
ps aux | grep fcitx5

# 2. 检查环境变量
env | grep IM_MODULE

# 3. 运行诊断
fcitx5-diagnose

# 4. 测试输入法
# 按 Ctrl+Space 激活，输入拼音测试
```

---

**配置完成后，重新登录系统，然后就可以使用 Fcitx5 + Rime 输入法了！**

**最后更新：** 2025-01-06


