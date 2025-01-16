<template>
  <div class="dashboard-container" @keydown.enter="focusInput">
    <div ref="messagesContainer" class="chat-container">
      <div v-for="(message, index) in messages" :key="index" 
           :class="['message', message.isAI ? 'ai' : 'user']">
        <div class="message-content" :class="{ 'markdown-body': message.isAI }">
          <div v-if="message.isAI" class="markdown-body">
            <!-- 调试信息 -->
            <pre v-if="false">{{ message.content }}</pre>
            
            <!-- 解析 JSON 字符串，检查是否包含数据库查询结果 -->
            <template v-if="isDbQueryResult(message.content)">
              <div v-html="renderMarkdown(getMessageHeader(message.content))" />
              
              <!-- 单值显示 -->
              <div v-if="isSingleValue(message.content)" class="single-value">
                <el-statistic 
                  :value="getSingleValue(message.content)"
                  :title="getStatTitle(message.content)"
                >
                  <template #suffix>
                    <el-icon><DataLine /></el-icon>
                  </template>
                </el-statistic>
              </div>
              
              <!-- 表格视图 -->
              <div v-else-if="getQueryResults(message.content).length > 0" class="query-results">
                <el-table 
                  :data="getQueryResults(message.content)"
                  style="width: 100%"
                  :border="true"
                  stripe
                >
                  <el-table-column 
                    v-for="col in getTableColumns(message.content)"
                    :key="col"
                    :prop="col"
                    :label="formatColumnLabel(col)"
                    show-overflow-tooltip
                  />
                </el-table>
              </div>
              
              <!-- SQL 语句展示 -->
              <div class="sql-preview">
                <div class="sql-header">
                  <el-icon><Connection /></el-icon>
                  执行的 SQL
                </div>
                <div v-html="renderMarkdown('```sql\n' + getQuerySQL(message.content) + '\n```')" />
              </div>
            </template>
            <div v-else v-html="renderMarkdown(message.content)" />
          </div>
          <div v-else>{{ message.content }}</div>
        </div>
        <div class="message-time">
          {{ new Date(message.time).toLocaleTimeString() }}
        </div>
      </div>
    </div>
    
    <div class="quick-tools">
      <el-button-group class="tool-group">
        <el-tooltip 
          content="查询天气" 
          placement="top"
          :show-after="500"
        >
          <el-button @click="quickCommand('天气 西安')" :icon="Sunny">
            天气查询
          </el-button>
        </el-tooltip>
        
        <el-tooltip 
          content="查看当前时间" 
          placement="top"
          :show-after="500"
        >
          <el-button @click="quickCommand('时间')" :icon="Timer">
            时间
          </el-button>
        </el-tooltip>
        
        <el-tooltip 
          content="查看所有任务" 
          placement="top"
          :show-after="500"
        >
          <el-button @click="quickCommand('任务列表')" :icon="List">
            任务列表
          </el-button>
        </el-tooltip>
        
        <el-tooltip 
          content="统计任务状态" 
          placement="top"
          :show-after="500"
        >
          <el-button @click="quickCommand('统计任务')" :icon="PieChart">
            任务统计
          </el-button>
        </el-tooltip>
      </el-button-group>
    </div>

    <div class="chat-input-container">
      <div v-if="showCommandHints" class="command-hints">
        <div class="hints-header">
          <el-icon><Operation /></el-icon>
          可用命令：
        </div>
        <div class="hints-content">
          <div 
            v-for="(commands, category) in filteredCommands" 
            :key="category" 
            class="hint-category"
          >
            <div class="category-title">{{ category }}：</div>
            <el-tag 
              v-for="cmd in commands" 
              :key="cmd"
              class="command-tag"
              @click="insertCommand(cmd)"
            >
              @{{ cmd }}
            </el-tag>
          </div>
        </div>
      </div>

      <el-input
        ref="messageInputRef"
        v-model="inputMessage"
        type="textarea"
        :rows="3"
        placeholder="发消息、输入 @ 触发命令"
        @input="handleInput"
        @keyup.enter.native.exact="sendMessage"
      />
      <el-button
        class="send-button"
        type="primary"
        :disabled="isLoading"
        @click="sendMessage"
      >
        <template #icon>
          <el-icon v-if="!isLoading"><Promotion /></el-icon>
          <el-icon v-else class="loading-icon"><Loading /></el-icon>
        </template>
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { 
  Promotion, 
  Loading, 
  Operation, 
  Connection, 
  DataLine,
  Sunny,
  Timer,
  List,
  PieChart
} from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

const ws = ref(null)
const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)
const messageInputRef = ref(null)
const showCommandHints = ref(false)
const filteredCommands = ref({})

// 可用命令配置
const availableCommands = {
  '任务管理': [
    '查询任务',
    '统计任务',
    '任务列表',
    '任务统计',
    '查找任务',
    '搜索任务'
  ],
  '天气查询': [
    '天气',
    '查天气',
    '查询天气'
  ],
  '时间查询': [
    '时间',
    '查时间',
    '当前时间',
    '现在时间'
  ]
}

// 处理输入
const handleInput = (value) => {
  // 检查是否需要显示命令提示
  const lastAtIndex = value.lastIndexOf('@')
  if (lastAtIndex !== -1) {
    const afterAt = value.slice(lastAtIndex + 1).trim().toLowerCase()
    showCommandHints.value = true
    
    // 根据输入筛选显示匹配的命令
    if (afterAt) {
      filteredCommands.value = {}
      Object.entries(availableCommands).forEach(([category, commands]) => {
        const filtered = commands.filter(cmd => cmd.toLowerCase().includes(afterAt))
        if (filtered.length > 0) {
          filteredCommands.value[category] = filtered
        }
      })
    } else {
      filteredCommands.value = availableCommands
    }
  } else {
    showCommandHints.value = false
  }
}

// 验证命令格式
const validateCommand = (text) => {
  if (!text.startsWith('@')) return { valid: true }
  
  const parts = text.slice(1).trim().split(/\s+/)
  const command = parts[0]
  
  // 查找命令所属类别
  let category = null
  Object.entries(availableCommands).forEach(([cat, commands]) => {
    if (commands.includes(command)) {
      category = cat
    }
  })
  
  if (!category) {
    return { valid: false, message: '未知的命令' }
  }
  
  // 验证命令参数
  switch (category) {
    case '天气查询':
      if (parts.length < 2) {
        return { valid: false, message: '请指定要查询的城市，例如：@天气 北京' }
      }
      break
    case '任务管理':
      if (parts.length < 1) {
        return { valid: false, message: '请指定查询条件，例如：@查询任务 pending' }
      }
      break
    case '时间查询':
      // 时间查询不需要额外参数
      break
  }
  
  return { valid: true }
}

// 插入命令
const insertCommand = (command) => {
  const cursorPosition = messageInputRef.value.textarea.selectionStart
  const textBeforeCursor = inputMessage.value.slice(0, cursorPosition)
  const lastAtIndex = textBeforeCursor.lastIndexOf('@')
  
  if (lastAtIndex !== -1) {
    // 替换@后面的内容
    inputMessage.value = 
      textBeforeCursor.slice(0, lastAtIndex) +
      '@' + command + ' ' +
      inputMessage.value.slice(cursorPosition)
    
    // 聚焦并移动光标
    nextTick(() => {
      messageInputRef.value.focus()
      const newPosition = lastAtIndex + command.length + 2
      messageInputRef.value.textarea.setSelectionRange(newPosition, newPosition)
    })
  }
  
  showCommandHints.value = false
}

// 初始化 markdown-it
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return '<pre class="hljs"><code>' +
               hljs.highlight(str, { language: lang, ignoreIllegals: true }).value +
               '</code></pre>'
      } catch (__) {}
    }
    return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>'
  }
})

// Markdown 渲染函数
const renderMarkdown = (content) => {
  try {
    return md.render(content)
  } catch (e) {
    console.error('Markdown rendering error:', e)
    return content
  }
}

// 连接WebSocket
const connectWebSocket = () => {
  ws.value = new WebSocket('ws://localhost:3001/ws')
  
  ws.value.onopen = () => {
    messages.value.push({
      content: '您好Zapz，小障已上线，今天也要当牛马吗？',
      isAI: true,
      time: new Date()
    })
  }
  
  ws.value.onmessage = (event) => {
    const data = JSON.parse(event.data)
    
    if (data.type === 'stream') {
      let content = data.content
      try {
        // 尝试解析 JSON 内容
        const jsonData = JSON.parse(data.content)
  
        if (jsonData.type === 'table' || jsonData.type === 'single') {
          // 这是数据库查询结果
          content = JSON.stringify(jsonData)
        } else if (jsonData.city) {
          // 格式化天气信息
          content = `### ${jsonData.message}\n\n` +
                   `- 温度：${jsonData.temperature}\n` +
                   `- 天气：${jsonData.weather}\n` +
                   `- 湿度：${jsonData.humidity}\n` +
                   `- 风力：${jsonData.wind}`
        } else if (jsonData.timestamp) {
          // 格式化时间信息
          content = `### 当前时间\n\n${jsonData.formatted}`
        }
      } catch (e) {
        content = data.content
      }
      
      // 处理流式响应
      if (messages.value.length > 0 && messages.value[messages.value.length - 1].isAI) {
        // 如果最后一条是AI消息，则追加内容
        messages.value[messages.value.length - 1].content += content
      } else {
        // 否则创建新消息
        messages.value.push({
          content: content,
          isAI: true,
          time: new Date()
        })
      }
    } else if (data.type === 'tool_calls') {
      // 处理工具调用
      console.log('收到工具调用:', {
        工具数量: data.tool_calls.length,
        调用详情: data.tool_calls.map(call => ({
          工具名称: call.function?.name,
          参数: call.function?.arguments
         }))
      })
    } else if (data.type === 'error') {
      messages.value.push({
        content: `错误: ${data.content}`,
        isAI: true,
        time: new Date()
      })
    }
    
    // 滚动到底部
    scrollToBottom()
  }
  
  ws.value.onclose = () => {
    messages.value.push({
      content: '连接已断开，正在重新连接...',
      isAI: true,
      time: new Date()
    })
    // 尝试重新连接
    setTimeout(connectWebSocket, 3000)
  }
  
  ws.value.onerror = (error) => {
    console.error('WebSocket error:', error)
    messages.value.push({
      content: '连接错误',
      isAI: true,
      time: new Date()
    })
  }
}

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return
  
  // 验证命令格式
  const validation = validateCommand(inputMessage.value)
  if (!validation.valid) {
    messages.value.push({
      content: validation.message,
      isAI: true,
      time: new Date()
    })
    return
  }
  
  isLoading.value = true
  try {
    // 关闭命令提示
    showCommandHints.value = false
    
    // 添加用户消息
    messages.value.push({
      content: inputMessage.value,
      isAI: false,
      time: new Date()
    })
    
    // 发送消息到服务器
    ws.value.send(JSON.stringify({
      messages: [{
        role: 'user',
        content: inputMessage.value
      }],
    }))
    
    // 清空输入
    inputMessage.value = ''
    
    // 滚动到底部
    scrollToBottom()
  } catch (error) {
    console.error('发送消息失败:', error)
    messages.value.push({
      content: '发送消息失败',
      isAI: true,
      time: new Date()
    })
  } finally {
    isLoading.value = false
  }
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 组件挂载时连接WebSocket
onMounted(() => {
  connectWebSocket()
  scrollToBottom()
  window.addEventListener('keydown', handleGlobalKeydown)
})

// 组件卸载时关闭WebSocket
onUnmounted(() => {
  if (ws.value) {
    ws.value.close()
  }
  window.removeEventListener('keydown', handleGlobalKeydown)
})

// 监听messages变化
watch(messages, () => {
  scrollToBottom()
}, { deep: true })

// 全局事件监听器
const handleGlobalKeydown = (event) => {
  if (event.key === 'Enter' && !event.ctrlKey && !event.shiftKey && !event.metaKey) {
    if (document.activeElement !== messageInputRef.value?.textarea) {
      event.preventDefault()
      focusInput()
    }
  }
}

// 聚焦输入框
const focusInput = () => {
  if (!isLoading.value) {
    messageInputRef.value?.focus()
  }
}

// 检查是否是数据库查询结果
const isDbQueryResult = (content) => {
  try {
    const data = JSON.parse(content)
    return data.type === 'table' || data.type === 'single'
  } catch (e) {
    return false
  }
}

// 获取消息头部（说明文字）
const getMessageHeader = (content) => {
  try {
    const data = JSON.parse(content)
    return data.message || ''
  } catch {
    return content
  }
}

// 获取查询结果
const getQueryResults = (content) => {
  try {
    const data = JSON.parse(content)
    if (data.type === 'table') {
      return Array.isArray(data.results) ? data.results : []
    }
    return []
  } catch {
    return []
  }
}

// 获取表格列
const getTableColumns = (content) => {
  const results = getQueryResults(content)
  if (results.length === 0) return []
  return Object.keys(results[0])
}

// 格式化列标签
const formatColumnLabel = (col) => {
  return col
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

// 检查是否是单值结果
const isSingleValue = (content) => {
  try {
    const data = JSON.parse(content)
    return data.type === 'single'
  } catch {
    return false
  }
}

// 获取单个值
const getSingleValue = (content) => {
  try {
    const data = JSON.parse(content)
    return data.results
  } catch {
    return null
  }
}

// 获取统计标题
const getStatTitle = (content) => {
  try {
    const data = JSON.parse(content)
    return data.message || '查询结果'
  } catch {
    return '查询结果'
  }
}

// 获取 SQL 语句
const getQuerySQL = (content) => {
  try {
    const data = JSON.parse(content)
    return data.sql || ''
  } catch {
    return ''
  }
}

// 快捷命令处理函数
const quickCommand = async (command) => {
  // 构造完整的命令
  const fullCommand = `@${command}`
  inputMessage.value = fullCommand
  
  // 直接发送消息
  await sendMessage()
}
</script>

<style scoped>
.dashboard-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 0;
}

.chat-container > * {
  margin-bottom: 16px;
}

.message {
  margin-bottom: 12px;
  max-width: 80%;
}

.message.user {
  margin-left: auto;
}

.message-content {
  font-size: 14px;
  padding: 10px 16px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.message.ai .message-content {
  background: #e3f2fd;
}

.message.user .message-content {
  background: #dcf8c6;
}

.message-time {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
  text-align: right;
}

.chat-input-container {
  position: relative;
  padding: 20px;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border-top: 1px solid #e4e7ed;
  margin-top: 20px;
}

.send-button {
  position: absolute;
  right: 30px;
  bottom: 30px;
  padding: 8px 16px;
  font-size: 14px;
  border-radius: 8px;
  background-color: var(--el-color-primary);
  color: #fff;
  transition: all 0.2s;
  width: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-button:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

/* 调整输入框样式 */
:deep(.el-textarea__inner) {
  padding-right: 100px;
  border-radius: 8px;
  resize: none;
  min-height: 100px;
  line-height: 1.5;
  border: 1px solid #e4e7ed;
  transition: border-color 0.2s;
}

:deep(.el-textarea__inner:focus) {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

/* 强制固定加载状态下的按钮样式 */
:deep(.el-button.is-loading) {
  width: 100px !important;
  padding-left: 16px !important;
  padding-right: 16px !important;
}

/* 修复 loading 图标导致的偏移 */
:deep(.el-button.is-loading .el-icon) {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

/* 隐藏默认的 loading 图标 */
:deep(.el-button.is-loading .el-icon--right) {
  display: none;
}

/* 确保文本内容居中 */
:deep(.el-button > span) {
  margin-left: 8px;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Markdown 样式 */
.markdown-body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  font-size: 14px;
  line-height: 1.6;
  word-wrap: break-word;
  background: transparent !important;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4 {
  margin-top: 16px;
  margin-bottom: 8px;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-body code {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}

.markdown-body pre {
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: rgba(0, 0, 0, 0.05) !important;
  border-radius: 3px;
  margin: 8px 0;
}

.markdown-body pre code {
  padding: 0;
  margin: 0;
  font-size: 100%;
  word-break: normal;
  white-space: pre;
  background: transparent;
  border: 0;
}

.markdown-body ul {
  padding-left: 2em;
  margin-top: 0;
  margin-bottom: 16px;
}

.markdown-body li {
  margin-top: 0.25em;
}

.markdown-body .hljs {
  background: transparent !important;
  padding: 0;
}

.markdown-body h3 {
  font-size: 1.2em;
  border-bottom: none;
  margin-top: 0;
}

.markdown-body h4 {
  font-size: 1.1em;
  margin-top: 12px;
}

:deep(.markdown-body p) {
  margin: 0;
}

.command-hints {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  position: absolute;
  bottom: 100%;
  left: 0;
  right: 0;
  z-index: 10;
}

.hints-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  margin-bottom: 12px;
  color: var(--el-text-color-primary);
}

.hints-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 200px;
  overflow-y: auto;
}

.hint-category {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 4px 0;
}

.category-title {
  font-weight: 500;
  color: var(--el-text-color-secondary);
  margin-right: 8px;
}

.command-tag {
  cursor: pointer;
  transition: all 0.2s;
  padding: 4px 8px;
}

.command-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  background-color: var(--el-color-primary-light-9);
}

/* 调整输入框提示文字样式 */
:deep(.el-textarea__inner::placeholder) {
  color: var(--el-text-color-secondary);
  font-style: italic;
}

.query-results {
  margin: 16px 0;
  border-radius: 8px;
  overflow: hidden;
}

.single-value {
  margin: 16px 0;
  padding: 16px;
  background: rgba(var(--el-color-primary-rgb), 0.1);
  border-radius: 8px;
}

.sql-preview {
  margin-top: 16px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
}

.sql-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

:deep(.el-table) {
  --el-table-border-color: var(--el-border-color-lighter);
  --el-table-header-bg-color: var(--el-fill-color-light);
}

:deep(.el-statistic__number) {
  font-size: 24px;
  font-weight: bold;
  color: var(--el-color-primary);
}

.quick-tools {
  padding: 12px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin: -10px 0 0px;
  position: relative;
  z-index: 1;
}

.tool-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

:deep(.el-button) {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.2s;
  min-width: 120px;
  justify-content: center;
}

:deep(.el-button:hover) {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.el-button .el-icon) {
  font-size: 16px;
}
</style> 