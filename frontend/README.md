# Server Agent Frontend

基于 Vue 3 + TypeScript + Element Plus 的现代化服务器管理系统前端。

## 技术栈

- **框架**: Vue 3.3+ (Composition API)
- **构建工具**: Vite 5
- **语言**: TypeScript
- **UI 框架**: Element Plus 2.4+
- **状态管理**: Pinia 2.1+
- **路由**: Vue Router 4.2+
- **HTTP 客户端**: Axios 1.6+
- **图表**: ECharts 5.4+ & vue-echarts
- **终端**: xterm.js 5.3+
- **国际化**: Vue I18n 9.8+
- **实时通信**: Socket.IO Client 4.6+
- **代码高亮**: highlight.js
- **Markdown 渲染**: markdown-it
- **日期处理**: dayjs

## 项目结构

```
frontend/
├── public/                    # 静态资源
├── src/
│   ├── api/                   # API 接口
│   │   ├── request.ts         # Axios 封装
│   │   ├── auth.ts            # 认证 API
│   │   ├── servers.ts         # 服务器管理 API
│   │   ├── metrics.ts         # 监控指标 API
│   │   ├── execute.ts         # 命令执行 API
│   │   ├── chat.ts            # AI 聊天 API
│   │   └── permissions.ts     # 权限管理 API
│   ├── assets/                # 资源文件
│   ├── components/            # 公共组件
│   │   ├── common/            # 通用组件
│   │   ├── server/            # 服务器相关组件
│   │   ├── chart/             # 图表组件
│   │   └── terminal/          # 终端组件
│   ├── layout/                # 布局组件
│   │   └── Layout.vue         # 主布局
│   ├── locales/               # 国际化
│   │   ├── zh-CN.json         # 中文
│   │   └── en-US.json         # 英文
│   ├── router/                # 路由配置
│   │   └── index.ts
│   ├── stores/                # Pinia 状态管理
│   │   ├── auth.ts            # 认证状态
│   │   └── servers.ts         # 服务器状态
│   ├── styles/                # 全局样式
│   ├── types/                 # TypeScript 类型
│   │   └── api.ts             # API 类型定义
│   ├── utils/                 # 工具函数
│   ├── views/                 # 页面组件
│   │   ├── Login.vue          # 登录页
│   │   ├── Register.vue       # 注册页
│   │   ├── servers/           # 服务器管理
│   │   │   ├── ServerList.vue
│   │   │   └── ServerDetail.vue
│   │   ├── monitoring/        # 监控面板
│   │   │   └── Dashboard.vue
│   │   ├── execute/           # 命令执行
│   │   │   └── CommandExecute.vue
│   │   ├── chat/              # AI 聊天
│   │   │   └── ChatInterface.vue
│   │   ├── permissions/       # 权限管理
│   │   │   └── PermissionManage.vue
│   │   ├── profile/           # 个人中心
│   │   │   └── UserProfile.vue
│   │   └── NotFound.vue       # 404 页面
│   ├── App.vue                # 根组件
│   └── main.ts                # 入口文件
├── .env                       # 环境变量
├── .env.development           # 开发环境
├── .env.production            # 生产环境
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## 已实现功能

### API 层 (100%)
- ✅ Axios 请求封装（拦截器、错误处理）
- ✅ 认证 API（登录、注册、token 刷新）
- ✅ 服务器管理 API（CRUD、连接测试）
- ✅ 监控指标 API（实时数据、历史数据、统计摘要）
- ✅ 命令执行 API（执行、验证、批量、历史）
- ✅ AI 聊天 API（发送消息、会话管理）
- ✅ 权限管理 API（授予、撤销、检查）

### 类型定义 (100%)
- ✅ 完整的 TypeScript 类型定义
- ✅ API 请求/响应类型
- ✅ 实体模型类型
- ✅ 分页类型

### 状态管理 (50%)
- ✅ 认证 Store（登录、注册、登出、刷新）
- ✅ 服务器 Store（CRUD 操作、状态管理）
- ⏳ 其他 Store（待实现）

### 路由配置 (100%)
- ✅ 路由定义和配置
- ✅ 路由守卫（认证检查、权限检查）
- ✅ 动态路由加载
- ✅ 页面标题管理

## 环境变量

创建 `.env.development` 文件：

```bash
# API 基础 URL
VITE_API_BASE_URL=http://localhost:8000/api/v1

# WebSocket URL
VITE_WS_URL=ws://localhost:8000

# 应用名称
VITE_APP_TITLE=Server Agent
```

创建 `.env.production` 文件：

```bash
VITE_API_BASE_URL=https://your-domain.com/api/v1
VITE_WS_URL=wss://your-domain.com
VITE_APP_TITLE=Server Agent
```

## 开发指南

### 安装依赖

```bash
cd frontend
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

### 代码检查

```bash
npm run lint
```

### 代码格式化

```bash
npm run format
```

## 页面说明

### 1. 登录/注册页面
- 用户登录
- 用户注册
- 表单验证
- 记住登录状态

### 2. 服务器管理
- 服务器列表（分页、搜索、筛选）
- 创建服务器（支持 SSH 密码和密钥）
- 编辑服务器信息
- 删除服务器
- 测试连接
- 服务器状态实时更新

### 3. 监控面板
- 实时性能指标（CPU、内存、磁盘、网络）
- 历史数据图表（ECharts）
- 多服务器对比
- 告警阈值设置

### 4. 命令执行
- 单服务器命令执行
- 批量命令执行
- 命令历史记录
- 危险命令警告
- 实时输出显示

### 5. AI 助手
- 自然语言交互
- 服务器管理对话
- 会话历史
- Markdown 消息渲染
- 代码高亮

### 6. 权限管理
- 用户权限列表
- 服务器权限配置
- 授予/撤销权限
- 权限级别（read, write, execute, admin）

### 7. 个人中心
- 用户信息展示
- 修改个人资料
- 修改密码
- 操作日志

## 组件开发规范

### 组件结构

```vue
<template>
  <div class="component-name">
    <!-- 组件内容 -->
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

// Props
interface Props {
  // props 定义
}

const props = defineProps<Props>()

// Emits
interface Emits {
  (e: 'event-name', value: any): void
}

const emit = defineEmits<Emits>()

// State
const state = ref()

// Computed
const computed值 = computed(() => {
  return state.value
})

// Methods
const method = () => {
  // 方法实现
}

// Lifecycle
onMounted(() => {
  // 挂载后执行
})
</script>

<style scoped lang="scss">
.component-name {
  // 样式
}
</style>
```

### API 调用

```typescript
import { useServersStore } from '@/stores/servers'
import { ElMessage } from 'element-plus'

const serversStore = useServersStore()

const loadData = async () => {
  try {
    await serversStore.fetchServers({ page: 1, size: 20 })
  } catch (error) {
    ElMessage.error('加载失败')
  }
}
```

### 类型安全

```typescript
import type { Server } from '@/types/api'

const server: Server = {
  id: '1',
  name: 'My Server',
  // ... 其他字段
}
```

## 待实现功能

### 高优先级
- [ ] 完成所有页面组件实现
- [ ] WebSocket 实时监控
- [ ] Web Terminal (xterm.js)
- [ ] 响应式布局优化

### 中优先级
- [ ] 主题切换（暗色模式）
- [ ] 更多图表类型
- [ ] 文件上传/下载
- [ ] 批量操作

### 低优先级
- [ ] PWA 支持
- [ ] 离线模式
- [ ] 数据导出
- [ ] 自定义仪表盘

## 性能优化

- ✅ 组件懒加载
- ✅ 路由懒加载
- ✅ Pinia 状态持久化
- ⏳ 虚拟滚动（大列表）
- ⏳ 图片懒加载
- ⏳ 请求防抖/节流

## 浏览器兼容性

- Chrome >= 90
- Firefox >= 88
- Safari >= 14
- Edge >= 90

## 相关资源

- [Vue 3 文档](https://cn.vuejs.org/)
- [Element Plus 文档](https://element-plus.org/zh-CN/)
- [Pinia 文档](https://pinia.vuejs.org/zh/)
- [Vue Router 文档](https://router.vuejs.org/zh/)
- [Vite 文档](https://cn.vitejs.dev/)
- [TypeScript 文档](https://www.typescriptlang.org/)

## 许可证

MIT
