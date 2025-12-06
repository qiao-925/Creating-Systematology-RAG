# Linux 输入法配置工具集

本文件夹包含 Linux 系统中文输入法的完整配置方案、安装脚本和详细教程。

## 📁 文件说明

### 📚 文档教程

| 文件 | 说明 |
|------|------|
| `FCITX5_RIME_TUTORIAL.md` | Fcitx5 + 中州韵（Rime）完整配置教程 |
| `IME_INSTALL_GUIDE.md` | 多输入法安装指南（Fcitx5、搜狗拼音等） |
| `LINUX_IME_COMPARISON.md` | Linux 中文输入法对比与推荐 |

### 🔧 安装脚本

| 文件 | 说明 | 用途 |
|------|------|------|
| `setup_fcitx5_rime.sh` | Fcitx5 + Rime 快速配置脚本 | 一键安装和配置 Fcitx5 + Rime |
| `install_ime_commands.sh` | 多输入法安装脚本 | 安装 Fcitx5 扩展输入法（五笔、Rime等）和 Fcitx4 |
| `install_multiple_ime.sh` | 完整多输入法安装脚本 | 安装多个输入法并配置环境变量 |
| `install_sogou_pinyin.sh` | 搜狗拼音安装脚本 | 安装搜狗拼音输入法（需要 Fcitx4） |

## 🚀 快速开始

### 方案一：Fcitx5 + Rime（推荐）

```bash
cd linux-ime-config
./setup_fcitx5_rime.sh
```

详细教程：查看 `FCITX5_RIME_TUTORIAL.md`

### 方案二：安装多个输入法

```bash
cd linux-ime-config
./install_ime_commands.sh
```

然后按照 `IME_INSTALL_GUIDE.md` 进行配置。

### 方案三：完整安装（包含搜狗拼音）

```bash
cd linux-ime-config
./install_multiple_ime.sh
```

## 📖 使用指南

### 1. 选择输入法方案

- **追求个性化/高级用户**：Fcitx5 + Rime
- **追求简单稳定**：Fcitx5 + Pinyin 或 IBus + libpinyin
- **习惯搜狗输入法**：Fcitx4 + 搜狗拼音
- **五笔用户**：Fcitx5 + 五笔

详细对比请查看：`LINUX_IME_COMPARISON.md`

### 2. 安装步骤

1. 选择合适的安装脚本执行
2. 配置环境变量（脚本会自动配置）
3. 在系统设置中选择默认输入法框架
4. 重新登录系统
5. 使用 `fcitx5-config-qt` 或 `fcitx-config-gtk` 配置输入法

### 3. 配置输入法

**Fcitx5 配置：**
```bash
fcitx5-config-qt
```

**Fcitx4 配置：**
```bash
fcitx-config-gtk
```

## 🔍 文件结构

```
linux-ime-config/
├── README.md                      # 本文件
├── FCITX5_RIME_TUTORIAL.md        # Fcitx5 + Rime 详细教程
├── IME_INSTALL_GUIDE.md           # 多输入法安装指南
├── LINUX_IME_COMPARISON.md        # 输入法对比与推荐
├── setup_fcitx5_rime.sh           # Fcitx5 + Rime 快速配置
├── install_ime_commands.sh        # 多输入法安装脚本
├── install_multiple_ime.sh        # 完整安装脚本
└── install_sogou_pinyin.sh        # 搜狗拼音安装脚本
```

## ⚙️ 环境变量说明

所有脚本会自动配置以下环境变量：

```bash
export GTK_IM_MODULE=fcitx5  # 或 fcitx（Fcitx4）
export QT_IM_MODULE=fcitx5   # 或 fcitx（Fcitx4）
export XMODIFIERS=@im=fcitx5 # 或 @im=fcitx（Fcitx4）
```

配置文件位置：
- `~/.xprofile` - X11 环境变量
- `~/.pam_environment` - 登录时加载
- `~/.bashrc` - Shell 环境变量（可选）

## 🐛 故障排查

### 输入法无法启动

```bash
# 检查环境变量
echo $GTK_IM_MODULE
echo $QT_IM_MODULE
echo $XMODIFIERS

# 诊断问题
fcitx5-diagnose  # Fcitx5
fcitx-diagnose   # Fcitx4
```

### 应用内无法输入中文

- 确保环境变量已设置
- 重启相关应用
- 检查应用启动脚本

### 配置不生效

- 重新登录系统
- 检查配置文件语法
- 重新部署 Rime：`fcitx5-rime --deploy`

## 📝 注意事项

1. **框架切换**：Fcitx5 和 Fcitx4 可以共存，但需要手动切换默认框架
2. **重新登录**：配置环境变量后必须重新登录才能生效
3. **搜狗拼音**：仅支持 Fcitx4，不支持 Fcitx5
4. **Wayland 支持**：Fcitx5 对 Wayland 支持更好

## 🔗 相关资源

- **Fcitx5 官网**：https://fcitx-im.org/
- **Rime 官网**：https://rime.im/
- **IBus 官网**：https://github.com/ibus/ibus
- **搜狗拼音**：https://pinyin.sogou.com/linux/

## 📋 脚本执行权限

如果脚本无法执行，请添加执行权限：

```bash
chmod +x *.sh
```

## 🎯 推荐阅读顺序

1. `LINUX_IME_COMPARISON.md` - 了解各输入法特点，选择适合自己的
2. `IME_INSTALL_GUIDE.md` - 查看安装指南
3. `FCITX5_RIME_TUTORIAL.md` - 如果选择 Rime，查看详细配置教程
4. 执行相应的安装脚本

---

**最后更新：** 2025-01-06

