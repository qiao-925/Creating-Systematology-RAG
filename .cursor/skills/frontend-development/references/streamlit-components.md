# Streamlit 原生组件详细说明

## 1. 文本与显示组件

| 组件 | 用途 | 示例 |
|------|------|------|
| `st.write()` | 通用文本显示 | `st.write("Hello")` |
| `st.markdown()` | Markdown 渲染 | `st.markdown("**Bold**")` |
| `st.title()` | 页面标题 | `st.title("My App")` |
| `st.header()` | 章节标题 | `st.header("Section 1")` |
| `st.subheader()` | 子标题 | `st.subheader("1.1")` |
| `st.caption()` | 辅助文本 | `st.caption("Note")` |
| `st.code()` | 代码块 | `st.code("print(1)", language="python")` |

## 2. 数据展示组件

| 组件 | 用途 | 示例 |
|------|------|------|
| `st.dataframe()` | 交互式表格 | `st.dataframe(df)` |
| `st.data_editor()` | 可编辑表格 | `st.data_editor(df)` |
| `st.table()` | 静态表格 | `st.table(df)` |
| `st.metric()` | 指标显示 | `st.metric("Users", 100, 10)` |
| `st.json()` | JSON 展示 | `st.json(data)` |

## 3. 输入组件

### 3.1 文本输入

```python
# 单行文本
name = st.text_input("Name")

# 多行文本
bio = st.text_area("Bio")
```

### 3.2 数字输入

```python
# 数字输入
age = st.number_input("Age", min_value=0, max_value=120)

# 滑块
value = st.slider("Value", 0, 100, 50)
```

### 3.3 选择输入

```python
# 单选
option = st.selectbox("Choose", ["A", "B", "C"])

# 多选
options = st.multiselect("Choose multiple", ["A", "B", "C"])

# 复选框
checked = st.checkbox("Agree")

# 单选按钮
choice = st.radio("Pick one", ["X", "Y"])
```

## 4. 布局组件

### 4.1 列布局

```python
col1, col2 = st.columns(2)
with col1:
    st.write("Left")
with col2:
    st.write("Right")
```

### 4.2 标签页

```python
tab1, tab2 = st.tabs(["Tab 1", "Tab 2"])
with tab1:
    st.write("Content 1")
with tab2:
    st.write("Content 2")
```

### 4.3 可展开区域

```python
with st.expander("Details"):
    st.write("Expanded content")
```

## 5. 聊天组件（Streamlit 1.28+）

```python
# 聊天消息
with st.chat_message("user"):
    st.write("Hello")

with st.chat_message("assistant"):
    st.write("Hi!")

# 聊天输入
prompt = st.chat_input("Say something")
```

## 6. 状态与反馈组件

```python
# 进度条
progress = st.progress(0)
progress.progress(50)

# 加载动画
with st.spinner("Loading..."):
    # 耗时操作
    pass

# 消息提示
st.success("Done!")
st.error("Error!")
st.warning("Warning!")
st.info("Info")

# 提示消息
st.toast("Saved!")
```

## 7. 何时考虑自定义组件

只有以下情况才考虑自定义组件：

| 需求 | 原生方案 | 需自定义 |
|------|----------|----------|
| 复杂图表 | `st.plotly_chart()` | 特殊交互 |
| 地图 | `st.map()` | 高级地图功能 |
| 富文本编辑 | `st.text_area()` | WYSIWYG 编辑器 |
| 拖拽排序 | 无 | ✅ 需要 |
