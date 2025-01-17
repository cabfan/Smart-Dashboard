<template>
  <div class="dashboard-container" @keydown.enter="focusInput">
    <div ref="messagesContainer" class="chat-container">
      <div v-for="(message, index) in messages" :key="index" 
           :class="['message', message.isAI ? 'ai' : 'user']">
        <div class="message-content" :class="{ 'markdown-body': message.isAI }">
          <div v-if="message.isAI" class="markdown-body">
            <!-- 加载状态 -->
            <div v-if="message.loading" class="loading-message">
              <el-skeleton :rows="3" animated />
              <div class="loading-text">
                <el-icon class="rotating"><Loading /></el-icon>
                正在查询数据，请稍候...
                <span class="timer">{{ formatExecutionTime(message.startTime) }}</span>
              </div>
            </div>
            
            <!-- 调试信息 -->
            <pre v-if="false">{{ message.content }}</pre>
            
            <!-- 解析 JSON 字符串，检查是否包含数据库查询结果 -->
            <template v-else-if="isQueryCommand(message.content)">
              <!-- 执行时间 -->
              <div class="execution-time">
                执行耗时: {{ calculateExecutionTime(message.startTime, message.endTime) }}
              </div>
              <div v-html="renderMarkdown(getMessageHeader(message.content))" />
              
              <!-- 数据可视化 -->
              <DataChart 
                v-if="shouldShowChart(message.content)"
                :data="parseMessageData(message.content)" 
              />
              
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
                  show-summary
                  :summary-method="getSummary"
                >
                  <el-table-column 
                    v-for="col in getTableColumns(message.content)"
                    :key="col"
                    :prop="col"
                    :label="formatColumnLabel(col)"
                    sortable
                    show-overflow-tooltip
                    :sort-method="(a, b) => sortTableColumn(a[col], b[col])"
                    :formatter="(row, column) => formatTableCell(row[column.property], column.property)"
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
    
    <!-- 快捷工具栏 -->
    <div class="quick-tools">
      <el-button-group class="tool-group">
        <!-- NBA 数据分析 -->
        <el-tooltip 
          content="查看各队投篮数据" 
          placement="top"
          :show-after="500"
        >
          <el-button @click="quickCommand('@查询统计 各队投篮命中率')" :icon="PieChart">
            球队命中率
          </el-button>
        </el-tooltip>
        
        <el-tooltip 
          content="查看不同区域投篮数据" 
          placement="top"
          :show-after="500"
        >
          <el-button @click="quickCommand('@查询统计 分析不同区域的投篮效率')" :icon="Position">
            区域分析
          </el-button>
        </el-tooltip>
        
        <el-tooltip 
          content="查看球员投篮排名" 
          placement="top"
          :show-after="500"
        >
          <el-button @click="quickCommand('@查询统计 球员投篮排名')" :icon="User">
            球员排名
          </el-button>
        </el-tooltip>
        
        <el-tooltip 
          content="查询天气" 
          placement="top"
          :show-after="500"
        >
          <el-button @click="quickCommand('@查天气 西安')" :icon="Sunny">
            天气查询
          </el-button>
        </el-tooltip>
        
        <el-tooltip 
          content="查看当前时间" 
          placement="top"
          :show-after="500"
        >
          <el-button @click="quickCommand('@查询时间')" :icon="Timer">
            时间
          </el-button>
        </el-tooltip>
        
        <el-tooltip 
          content="查看待办任务列表" 
          placement="top"
          :show-after="500"
        >
          <el-button @click="quickCommand('@查询统计 查看所有待办任务')" :icon="List">
            待办任务
          </el-button>
        </el-tooltip>
      </el-button-group>
    </div>
    
    <!-- 输入区域 -->
    <div class="chat-input-container">
      <!-- 命令提示 -->
      <div v-if="showCommandHints" class="command-hints">
        <!-- 关闭按钮 -->
        <el-button
          class="close-hints"
          type="text"
          :icon="Close"
          @click="showCommandHints = false"
        />
        <div class="hints-header">
          <el-icon><Operation /></el-icon>
          可用命令
        </div>
        <div class="hints-content">
          <!-- 基础命令 -->
          <div class="hint-category">
            <span class="category-title">基础命令</span>
            <div class="command-group">
              <el-tag 
                v-for="cmd in baseCommands" 
                :key="cmd"
                class="command-tag command-base"
                @click="applyCommand(cmd)"
              >
                {{ cmd }}
              </el-tag>
            </div>
          </div>
          
          <!-- 分类示例命令 -->
          <div class="categories-row">
            <div class="category-container" v-if="commandCategories['基础查询']">
              <span class="category-title">基础查询</span>
              <div class="command-group">
                <el-tag 
                  v-for="cmd in commandCategories['基础查询']"
                  :key="cmd"
                  class="command-tag command-example"
                  @click="applyCommand(cmd)"
                >
                  {{ cmd }}
                </el-tag>
              </div>
            </div>
            <div class="category-container" v-if="commandCategories['球队分析']">
              <span class="category-title">球队分析</span>
              <div class="command-group">
                <el-tag 
                  v-for="cmd in commandCategories['球队分析']"
                  :key="cmd"
                  class="command-tag command-example"
                  @click="applyCommand(cmd)"
                >
                  {{ cmd }}
                </el-tag>
              </div>
            </div>
          </div>
          
          <!-- 第二行：球员分析和区域分析 -->
          <div class="categories-row">
            <div class="category-container" v-if="commandCategories['球员分析']">
              <span class="category-title">球员分析</span>
              <div class="command-group">
                <el-tag 
                  v-for="cmd in commandCategories['球员分析']"
                  :key="cmd"
                  class="command-tag command-example"
                  @click="applyCommand(cmd)"
                >
                  {{ cmd }}
                </el-tag>
              </div>
            </div>
            <div class="category-container" v-if="commandCategories['区域分析']">
              <span class="category-title">区域分析</span>
              <div class="command-group">
                <el-tag 
                  v-for="cmd in commandCategories['区域分析']"
                  :key="cmd"
                  class="command-tag command-example"
                  @click="applyCommand(cmd)"
                >
                  {{ cmd }}
                </el-tag>
              </div>
            </div>
          </div>
          
          <!-- 第三行：系统功能 -->
          <div class="categories-row">
            <div class="category-container" v-if="commandCategories['系统功能']">
              <span class="category-title">{{ category }}</span>
              <div class="command-group">
                <el-tag 
                  v-for="cmd in commandCategories['系统功能']"
                  :key="cmd"
                  class="command-tag command-example"
                  @click="applyCommand(cmd)"
                >
                  {{ cmd }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <el-input
        v-model="inputMessage"
        type="textarea"
        :rows="3"
        placeholder="输入 @ 查看可用命令..."
        resize="none"
        @keydown.enter.prevent="sendMessage"
        @input="handleInput"
        ref="inputRef"
      />
      
      <el-button 
        type="primary" 
        class="send-button"
        :loading="isLoading"
        @click="sendMessage"
      >
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import DataChart from '../components/DataChart.vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import { 
  Promotion, 
  Loading, 
  Operation, 
  Connection,
  DataLine,
  Sunny,
  Timer,
  List,
  PieChart,
  Position,
  User,
  Close
} from '@element-plus/icons-vue'

// 初始化 markdown 解析器
const md = new MarkdownIt({
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value
      } catch (__) {}
    }
    return ''
  }
})

// 响应式状态
const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const ws = ref(null)
const showCommandHints = ref(false)
const inputRef = ref(null)
const messagesContainer = ref(null)

// 基础命令和示例命令
const baseCommands = [
  '@查询统计',
  '@查天气',
  '@查询时间'
]

const exampleCommands = [
  // NBA 数据分析示例
  '@查询统计 各队投篮命中率',
  '@查询统计 分析不同区域的投篮效率',
  '@查询统计 球员投篮排名',
  '@查询统计 总共多少次投篮',
  '@查询统计 投篮命中率最高的前10名球员',
  '@查询统计 三分球命中率最高的球队',
  '@查询统计 各区域投篮次数分布',
  
  // 系统功能示例
  '@查天气 西安',
  '@查询时间',
  '@查询统计 查看所有待办任务'
]

// 命令提示分类
const commandCategories = {
  '基础查询': [
    '@查询统计 总共多少次投篮',
    '@查询统计 查看所有待办任务'
  ],
  '球队分析': [
    '@查询统计 各队投篮命中率',
    '@查询统计 三分球命中率最高的球队'
  ],
  '球员分析': [
    '@查询统计 球员投篮排名',
    '@查询统计 投篮命中率最高的前10名球员'
  ],
  '区域分析': [
    '@查询统计 分析不同区域的投篮效率',
    '@查询统计 各区域投篮次数分布'
  ],
  '系统功能': [
    '@查天气 西安',
    '@查询时间'
  ]
}

// 格式化执行时间（用于实时显示）
const formatExecutionTime = (startTime) => {
  if (!startTime) return '0.0s'
  const elapsed = (Date.now() - startTime) / 1000
  return elapsed.toFixed(1) + 's'
}

// 计算最终执行时间
const calculateExecutionTime = (startTime, endTime) => {
  if (!startTime || !endTime) return '0.0s'
  const elapsed = (endTime - startTime) / 1000
  return elapsed.toFixed(1) + 's'
}

// WebSocket 连接
const connectWebSocket = () => {
  ws.value = new WebSocket('ws://localhost:3001/ws')
  
  ws.value.onopen = () => {
    messages.value.push({
      content: '您好，我是您的智能助手。请问有什么可以帮您？',
      isAI: true,
      time: new Date()
    })
  }
  
  ws.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      const lastMessage = messages.value[messages.value.length - 1]
      
      if (data.type === 'stream') {
        if (lastMessage && lastMessage.isAI) {
          if (data.content) {
            if (typeof data.content === 'string' && data.content.startsWith('{')) {
              // 如果内容是 JSON 字符串，直接设置
              lastMessage.content = data.content
              lastMessage.loading = false
              lastMessage.endTime = Date.now()
            } else {
              // 普通文本，追加内容
              lastMessage.content += data.content
            }
          } else {
            lastMessage.content += data.content
          }
        }
      }
      
      scrollToBottom()
    } catch (error) {
      console.error('Error handling WebSocket message:', error)
    }
  }
  
  ws.value.onerror = (error) => {
    console.error('WebSocket error:', error)
    ElMessage.error('连接错误，请刷新页面重试')
  }
}

// API 配置
const API_BASE_URL = 'http://localhost:3001'

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return
  
  try {
    isLoading.value = true
    showCommandHints.value = false
    const userMessage = inputMessage.value.trim()
    
    // 提取命令内容
    const commandMatch = userMessage.match(/@([^@]+)/)
    const commandContent = commandMatch ? commandMatch[1].trim() : userMessage
    
    // 判断命令类型
    const isQueryCommand = commandContent.startsWith('查询统计')
    const isTimeQuery = commandContent.startsWith('查询时间')
    const isWeatherQuery = commandContent.startsWith('查天气')
    const isSpecialCommand = isQueryCommand || isTimeQuery || isWeatherQuery
    
    // 添加用户消息
    messages.value.push({
      content: userMessage,
      isAI: false,
      time: new Date()
    })
    
    // 添加 AI 消息
    messages.value.push({
      content: '',
      isAI: true,
      loading: isSpecialCommand,
      startTime: Date.now(),
      time: new Date()
    })
    
    inputMessage.value = ''
    await nextTick()
    scrollToBottom()
    
    // 处理时间查询
    if (isTimeQuery) {
      try {
        const response = await fetch('/api/current-time')
        const data = await response.json()
        console.log('Time API response:', data)
        if (data.success) {
          const lastMessage = messages.value[messages.value.length - 1]
          lastMessage.content = JSON.stringify({
            type: 'time',
            formatted: data.formatted,
            timestamp: data.timestamp
          })
          lastMessage.loading = false
          lastMessage.endTime = Date.now()
        } else {
          throw new Error(data.error || '获取时间失败')
        }
        return
      } catch (error) {
        console.error('Error fetching time:', error)
        const lastMessage = messages.value[messages.value.length - 1]
        lastMessage.content = '获取时间失败：' + error.message
        lastMessage.loading = false
        lastMessage.endTime = Date.now()
        ElMessage.error('获取时间失败：' + error.message)
        return
      }
    }
    
    // 发送消息到服务器
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({
        messages: [{
          role: 'user',
          content: commandMatch ? `@${commandContent}` : userMessage
        }]
      }))
    }
  } catch (error) {
    console.error('Error sending message:', error)
  } finally {
    isLoading.value = false
  }
}

// 处理输入
const handleInput = (value) => {
  // 检查是否刚输入了 @ 符号
  const lastChar = value.slice(-1)
  if (lastChar === '@') {
    showCommandHints.value = true
  } else {
    showCommandHints.value = false
  }
}

// 应用命令
const applyCommand = (command) => {
  inputMessage.value = command
  // 选择命令后自动隐藏提示
  setTimeout(() => {
    showCommandHints.value = false
  }, 100)
  inputRef.value.focus()
}

// 快捷命令
const quickCommand = (command) => {
  inputMessage.value = command
  showCommandHints.value = false
  sendMessage()
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 判断消息类型的工具函数
const isQueryCommand = (content) => {
  try {
    if (!content) return false
    const data = JSON.parse(content)
    // 检查是否包含必要的查询结果字段
    return data.sql && (
      // 数组类型的结果
      (Array.isArray(data.results) && Array.isArray(data.columns)) ||
      // 单值类型的结果
      (data.type === 'single' && typeof data.results === 'number')
    )
  } catch {
    return false
  }
}

const isDbQueryResult = (content) => {
  try {
    if (!content) return false
    const data = JSON.parse(content)
    // 检查是否是数据库查询结果或特殊格式（天气、时间等）
    return data.hasOwnProperty('sql') || 
           data.hasOwnProperty('results') ||
           data.hasOwnProperty('type') ||
           data.hasOwnProperty('formatted')  // 用于时间显示
  } catch {
    return false
  }
}

const renderMarkdown = (content) => {
  try {
    // 尝试解析 JSON，如果是特殊格式数据，进行格式化
    const data = JSON.parse(content)
    // 处理不同类型的消息
    if (data.type === 'time') {
      const timeMarkdown = `## 当前时间\n\n**${data.formatted}**\n\n*时区：北京时间 (UTC+8)*`
      return md.render(timeMarkdown)
    } else if (data.weather) {
      const weatherInfo = []
      if (data.city) weatherInfo.push(`- 城市：${data.city}`)
      if (data.weather) weatherInfo.push(`- 天气：${data.weather}`)
      if (data.temperature) weatherInfo.push(`- 温度：${data.temperature}°C`)
      if (data.humidity) weatherInfo.push(`- 湿度：${data.humidity}%`)
      if (data.wind_direction) weatherInfo.push(`- 风向：${data.wind_direction}`)
      if (data.wind_scale) weatherInfo.push(`- 风力：${data.wind_scale}级`)
      if (data.update_time) weatherInfo.push(`- 更新时间：${data.update_time}`)
      
      const weatherMarkdown = `## 天气信息\n\n${weatherInfo.join('\n')}`
      return md.render(weatherMarkdown)
    } else if (data.type === 'query') {
      // 查询结果显示消息部分
      return md.render(data.message || '')
    }
  } catch {
    // 如果解析失败，按普通文本处理
    return md.render(content || '')
  }
  return md.render(content || '')
}

const getMessageHeader = (content) => {
  try {
    const data = JSON.parse(content)
    return data.message || ''
  } catch {
    return content
  }
}

const getQuerySQL = (content) => {
  try {
    const data = JSON.parse(content)
    return data.sql || ''
  } catch {
    return ''
  }
}

const getQueryResults = (content) => {
  try {
    const data = JSON.parse(content)
    // 如果是单值结果，转换为表格格式
    if (data.type === 'single' && typeof data.results === 'number') {
      return [{
        [data.columns[0]]: data.results
      }]
    }
    // 数组类型的结果
    return Array.isArray(data.results) ? data.results : []
  } catch {
    return []
  }
}

const getTableColumns = (content) => {
  try {
    const data = JSON.parse(content)
    // 确保返回的是数组
    return Array.isArray(data.columns) ? data.columns : 
           (data.columns ? [data.columns] : [])
  } catch {
    return []
  }
}

const formatColumnLabel = (column) => {
  return column
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

const sortTableColumn = (a, b) => {
  if (typeof a === 'number' && typeof b === 'number') {
    return a - b
  }
  return String(a).localeCompare(String(b))
}

const getSummary = (param) => {
  const { columns, data } = param
  const sums = []
  columns.forEach((column, index) => {
    if (index === 0) {
      sums[index] = '合计'
      return
    }
    const values = data.map(item => Number(item[column.property]))
    if (!values.every(value => isNaN(value))) {
      sums[index] = values.reduce((prev, curr) => {
        const value = Number(curr)
        if (!isNaN(value)) {
          return prev + curr
        } else {
          return prev
        }
      }, 0)
    } else {
      sums[index] = ''
    }
  })
  return sums
}

// 工具函数
const shouldShowChart = (content) => {
  try {
    if (!content) return false
    const data = JSON.parse(content)
    // 检查是否有数值列
    const hasNumericColumn = data.columns?.some(col => 
      col.toLowerCase().includes('count') ||
      col.toLowerCase().includes('percentage') ||
      col.toLowerCase().includes('rate') ||
      col.toLowerCase().includes('amount')
    )
    // 检查是否是统计类查询
    const isStatQuery = data.sql?.toLowerCase().includes('group by') ||
                       data.sql?.toLowerCase().includes('count') ||
                       data.sql?.toLowerCase().includes('sum') ||
                       data.sql?.toLowerCase().includes('avg')
    return hasNumericColumn && isStatQuery
  } catch {
    return false
  }
}

// 解析消息数据用于图表显示
const parseMessageData = (content) => {
  try {
    const data = JSON.parse(content)
    return {
      results: data.results || [],
      columns: data.columns || [],
      type: data.type || 'table'
    }
  } catch {
    return {
      results: [],
      columns: [],
      type: 'table'
    }
  }
}

// 格式化表格单元格
const formatTableCell = (value, column) => {
  if (value === null || value === undefined) {
    return '-'
  }
  
  // 如果是 zone/player/team 等文本列，直接返回原值
  if (['zone', 'player', 'team', 'player_name', 'team_name'].includes(column.toLowerCase())) {
    return value
  }
  
  // 检查是否是日期
  const dateValue = new Date(value)
  if (!isNaN(dateValue.getTime()) && column.toLowerCase().includes('date')) {
    return dateValue.toLocaleDateString()
  }
  
  // 检查是否是百分比
  if (typeof value === 'number' && 
      (column.toLowerCase().includes('percentage') || 
       column.toLowerCase().includes('ratio') || 
       column.toLowerCase().includes('rate'))) {
    return value.toFixed(2) + '%'
  }
  
  // 检查是否是大数值
  if (typeof value === 'number' && Math.abs(value) >= 1000) {
    return value.toLocaleString()
  }
  
  return value
}

// 工具函数
const isSingleValue = (content) => {
  try {
    const data = JSON.parse(content)
    return data.type === 'single' && typeof data.results === 'number'
  } catch {
    return false
  }
}

const getSingleValue = (content) => {
  try {
    const data = JSON.parse(content)
    // 格式化大数字
    if (typeof data.results === 'number') {
      return data.results.toLocaleString()
    }
    return data.results || ''
  } catch {
    return null
  }
}

const getStatTitle = (content) => {
  try {
    const data = JSON.parse(content)
    return data.message || ''
  } catch {
    return ''
  }
}

// 添加定时器来更新加载时间
const updateTimer = ref(null)

// 监听消息列表变化
watch(messages, (newMessages) => {
  // 清除之前的定时器
  if (updateTimer.value) {
    clearInterval(updateTimer.value)
  }
  
  // 查找正在加载的消息
  const loadingMessage = newMessages.find(msg => msg.loading)
  if (loadingMessage) {
    // 创建新的定时器，每 100ms 更新一次
    updateTimer.value = setInterval(() => {
      // 强制更新组件
      messages.value = [...messages.value]
    }, 100)
  }
}, { deep: true })

// 在组件卸载时清理定时器
onUnmounted(() => {
  if (updateTimer.value) {
    clearInterval(updateTimer.value)
  }
})

// 生命周期钩子
onMounted(() => {
  connectWebSocket()
  scrollToBottom()
})

onUnmounted(() => {
  if (ws.value) {
    ws.value.close()
  }
})
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
  margin-bottom: 20px;
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
  top: -12px;
  transform: translateY(-100%);
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
  max-height: 300px;
  overflow-y: auto;
}

.categories-row {
  display: flex;
  gap: 24px;
}

.category-container {
  flex: 1;
  min-width: 0;  /* 防止flex子项溢出 */
}

.hint-category {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 4px 0;
}

.category-title {
  font-weight: 500;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
  font-size: 0.9em;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.command-tag {
  cursor: pointer;
  transition: all 0.2s;
  padding: 3px 8px;
  margin: 2px;
  white-space: nowrap;
  max-width: calc(50% - 4px);  /* 每行显示2个 */
  overflow: hidden;
  text-overflow: ellipsis;
}

.command-group {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.command-base {
  font-weight: 600;
  background-color: var(--el-color-primary-light-8);
  border-color: var(--el-color-primary-light-5);
  color: var(--el-color-primary);
  max-width: none;  /* 基础命令不限制宽度 */
}

.command-example {
  background-color: var(--el-fill-color-light);
  border-color: var(--el-border-color-lighter);
  color: var(--el-text-color-regular);
  font-size: 0.85em;
}

.command-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.command-base:hover {
  background-color: var(--el-color-primary-light-7);
}

.command-example:hover {
  background-color: var(--el-fill-color);
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

.loading-message {
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.loading-text {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  color: var(--el-text-color-secondary);
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.execution-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.timer {
  font-family: monospace;
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  margin-left: auto;
}

.close-hints {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 4px;
  color: var(--el-text-color-secondary);
}

.close-hints:hover {
  color: var(--el-text-color-primary);
}
</style> 