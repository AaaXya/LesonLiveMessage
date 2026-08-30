# Vue DevUI 组件使用指南 - 配色方案集成

本指南展示如何使用Vue DevUI组件，并与新的治愈系配色方案（60-30-10法则）集成。

## 配色方案概览

- **主色（60%）**：米白色背景 (#F5F2ED - Light) / 温暖深色 (#1A1815 - Dark)
- **辅助色（30%）**：卡片背景、边框、标签
- **强调色（10%）**：活力绿 (#6FB969)、清爽蓝绿 (#5ECCC4)、柔和蓝 (#8FB1D5)

---

## DevUI 核心组件

### 1. Button（按钮）

```vue
<!-- 主操作按钮 - 使用强调色 -->
<d-button variant="solid" color="primary">
  开始监听
</d-button>

<!-- 次操作按钮 - 使用outline样式 -->
<d-button variant="outline" color="secondary">
  停止监听
</d-button>

<!-- 危险操作 -->
<d-button variant="solid" color="danger">
  删除
</d-button>

<!-- 禁用状态 -->
<d-button :disabled="isLoading">
  {{ isLoading ? '加载中...' : '确定' }}
</d-button>
```

**样式特点**：

- 主按钮使用绿色渐变 (#6FB969 → #5ECCC4)
- 具有hover时的向上浮起效果
- 圆角8px，增强现代感

### 2. Card（卡片）

```vue
<!-- 基础卡片 -->
<d-card class="room-card">
  <template #default>
    <h3>直播间标题</h3>
    <p>房间信息</p>
  </template>
</d-card>

<!-- 带标题和操作的卡片 -->
<d-card title="数据列表" class="data-card">
  <template #extra>
    <d-button variant="outline">导出</d-button>
  </template>
  <table class="data-table">
    <!-- ... -->
  </table>
</d-card>
```

**样式特点**：

- 背景使用辅助色 (#FDFBF8 - Light)
- 边框使用柔和灰色
- 支持响应式布局

### 3. Input（输入框）

```vue
<!-- 文本输入 -->
<input v-model="roomId" class="control" placeholder="输入直播间ID" />

<!-- 带验证的输入 -->
<input v-model="email" class="control" type="email" :disabled="isReadonly" />

<!-- 搜索输入 -->
<input v-model="keyword" class="control" placeholder="搜索关键词" @keyup.enter="handleSearch" />
```

**样式特点**：

- 圆角8px，边框使用 var(--border)
- Focus状态显示绿色高亮
- 背景透明度处理

### 4. Select（下拉框）

```vue
<!-- 主题选择 -->
<select v-model="theme" class="control">
  <option value="dark">深色</option>
  <option value="light">浅色</option>
</select>

<!-- 房间选择 -->
<select v-model="selectedRoom" class="control" @change="handleRoomChange">
  <option v-for="room in rooms" :key="room.id" :value="room.id">
    {{ room.title }}
  </option>
</select>
```

### 5. Checkbox 和 Radio

```vue
<!-- 复选框 -->
<label>
  <input v-model="features.enable_alerts" type="checkbox" />
  启用警报
</label>

<!-- 单选框 -->
<label>
  <input v-model="openMode" type="radio" value="window" />
  窗口模式
</label>
```

### 6. Badge（徽章）

```vue
<!-- 状态徽章 -->
<span class="badge success">直播中</span>
<span class="badge warning">连接中</span>
<span class="badge danger">错误</span>

<!-- 数据徽章 -->
<span class="badge">
  {{ danmuCount }} 条弹幕
</span>
```

**可用类**：`success`、`warning`、`danger`（在base.css中定义）

---

## 组件合成示例

### 列表视图模式

```vue
<template>
	<div class="view-container">
		<!-- 搜索栏 -->
		<div class="toolbar">
			<input v-model="keyword" class="control" placeholder="搜索..." />
			<select v-model="filter" class="control">
				<option value="">全部</option>
				<option value="active">活跃</option>
			</select>
			<d-button color="primary" @click="handleSearch">搜索</d-button>
		</div>

		<!-- 列表卡片 -->
		<d-card v-for="item in items" :key="item.id" class="item-card">
			<div class="item-header">
				<h3>{{ item.title }}</h3>
				<span class="badge" :class="item.status">{{ item.statusLabel }}</span>
			</div>
			<p class="item-desc">{{ item.description }}</p>
			<div class="item-actions">
				<d-button variant="solid" color="primary" @click="handleEdit(item)">
					编辑
				</d-button>
				<d-button variant="outline" color="secondary" @click="handleDelete(item)">
					删除
				</d-button>
			</div>
		</d-card>

		<!-- 分页 -->
		<d-pagination v-model="page" :total="total" :page-size="pageSize" />
	</div>
</template>

<style scoped>
.view-container {
	display: grid;
	gap: 16px;
}

.toolbar {
	display: flex;
	gap: 8px;
	flex-wrap: wrap;
}

.toolbar input,
.toolbar select {
	flex: 1;
	min-width: 150px;
}

.item-card {
	display: grid;
	gap: 12px;
}

.item-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.item-header h3 {
	margin: 0;
	color: var(--text-primary);
}

.item-desc {
	margin: 0;
	color: var(--text-muted);
	font-size: 13px;
}

.item-actions {
	display: flex;
	gap: 8px;
}
</style>
```

### 表单视图模式

```vue
<template>
	<d-card class="form-card" title="设置表单">
		<form class="form" @submit.prevent="handleSubmit">
			<!-- 文本字段 -->
			<label class="form-group">
				<span class="label-text">直播间ID</span>
				<input v-model="form.roomId" class="control" type="number" required />
			</label>

			<!-- 下拉选择 -->
			<label class="form-group">
				<span class="label-text">主题</span>
				<select v-model="form.theme" class="control">
					<option value="dark">深色</option>
					<option value="light">浅色</option>
				</select>
			</label>

			<!-- 复选框组 -->
			<div class="form-group">
				<span class="label-text">功能开关</span>
				<div class="checkbox-group">
					<label v-for="feature in features" :key="feature.key">
						<input v-model="form.features[feature.key]" type="checkbox" />
						{{ feature.label }}
					</label>
				</div>
			</div>

			<!-- 标签输入 -->
			<div class="form-group">
				<span class="label-text">过滤词</span>
				<div class="tag-input">
					<input
						v-model="newTag"
						class="control"
						placeholder="输入后回车"
						@keyup.enter="addTag"
					/>
					<d-button variant="outline" @click="addTag">添加</d-button>
				</div>
				<div class="tags">
					<span v-for="(tag, i) in form.tags" :key="tag" class="badge">
						{{ tag }}
						<button @click="removeTag(i)">×</button>
					</span>
				</div>
			</div>

			<!-- 按钮组 -->
			<div class="form-actions">
				<d-button variant="solid" color="primary" type="submit"> 保存 </d-button>
				<d-button variant="outline" @click="handleReset"> 重置 </d-button>
			</div>
		</form>
	</d-card>
</template>

<style scoped>
.form-card {
	max-width: 600px;
}

.form {
	display: grid;
	gap: 16px;
}

.form-group {
	display: grid;
	gap: 6px;
}

.label-text {
	font-size: 13px;
	font-weight: 600;
	color: var(--text-muted);
}

.checkbox-group {
	display: grid;
	grid-template-columns: repeat(2, 1fr);
	gap: 8px;
}

.checkbox-group label {
	display: flex;
	align-items: center;
	gap: 6px;
	color: var(--text-primary);
}

.tag-input {
	display: flex;
	gap: 8px;
}

.tag-input input {
	flex: 1;
}

.tags {
	display: flex;
	flex-wrap: wrap;
	gap: 6px;
}

.tags .badge button {
	margin-left: 4px;
	border: none;
	background: none;
	cursor: pointer;
	color: inherit;
}

.form-actions {
	display: flex;
	gap: 8px;
	margin-top: 12px;
}
</style>
```

---

## 色彩应用规范

### 强调色使用场景

| 颜色 | 值      | 使用场景               |
| ---- | ------- | ---------------------- |
| 绿色 | #6FB969 | 主操作、确认、成功状态 |
| 蓝绿 | #5ECCC4 | 次操作、信息提示       |
| 蓝色 | #8FB1D5 | 链接、补充信息         |
| 橙色 | #D8937D | 警告、需要注意         |
| 红色 | #D97676 | 危险、删除、错误       |

### CSS变量应用

```css
/* 文本 */
color: var(--text-primary); /* 主文本 */
color: var(--text-muted); /* 次要文本 */
color: var(--text-placeholder); /* 占位符文本 */

/* 背景 */
background: var(--bg); /* 主背景 */
background: var(--surface); /* 卡片背景 */
background: var(--surface-hover); /* 悬停背景 */

/* 边框与分割线 */
border-color: var(--border); /* 普通边框 */
border-color: var(--border-strong); /* 强调边框 */

/* 状态色 */
color: var(--success); /* 成功 */
color: var(--warning); /* 警告 */
color: var(--danger); /* 危险 */
```

---

## 响应式设计

所有组件应支持移动设备。示例：

```vue
<style scoped>
.container {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
	gap: 16px;
}

/* 平板 */
@media (max-width: 768px) {
	.container {
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 12px;
	}
}

/* 手机 */
@media (max-width: 480px) {
	.container {
		grid-template-columns: 1fr;
		gap: 8px;
	}
}
</style>
```

---

## 最佳实践

1. **一致的间距**：使用8px、12px、16px、24px的倍数
2. **清晰的层级**：利用color、font-size、font-weight区分
3. **充足的对比度**：确保文本可读性（WCAG AA标准）
4. **状态反馈**：鼠标悬停、焦点、禁用状态要明确
5. **无障碍性**：使用语义HTML标签，提供aria标签
6. **性能优化**：使用CSS变量减少样式计算

---

## 主题切换

主题在运行时可切换（浅色/深色模式）：

```javascript
// 切换浅色模式
document.documentElement.classList.add('light')
localStorage.setItem('color-mode', 'light')

// 恢复深色模式
document.documentElement.classList.remove('light')
localStorage.setItem('color-mode', 'dark')
```

AppLayout中的切换按钮已集成此功能。

---

## 导入和初始化

在 `main.js` 中已配置：

```javascript
import DevUI from 'vue-devui'
import 'vue-devui/style.css'
import './styles/base.css'
import './styles/devui-theme.css'

app.use(DevUI)
```

所有DevUI组件可直接使用（无需额外导入）。
