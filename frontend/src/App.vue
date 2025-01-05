<template>
  <div class="app-container">
    <!-- 侧边栏 -->
    <nav class="sidebar">
      <div class="logo">
        <h2>Smart Dashboard</h2>
      </div>
      <div class="menu">
        <div class="menu-item active">
          <el-icon><ChatLineRound /></el-icon>
          <span>智能助手</span>
        </div>
        <div class="menu-item">
          <el-icon><DataLine /></el-icon>
          <span>数据概览</span>
        </div>
        <div class="menu-item">
          <el-icon><List /></el-icon>
          <span>任务列表</span>
        </div>
        <div class="menu-item">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </div>
      </div>
    </nav>

    <!-- 主内容区 -->
    <main class="main">
      <!-- 头部 -->
      <header class="header">
        <div class="breadcrumb">
          <span>首页</span>
          <span class="separator">/</span>
          <span>智能助手</span>
        </div>
        <div class="header-actions">
          <el-button type="primary" plain size="small">
            <el-icon><Bell /></el-icon>
          </el-button>
          <el-avatar class="avatar" :size="32" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png" />
        </div>
      </header>

      <!-- 聊天区域 -->
      <div class="chat">
        <div class="chat-messages" ref="messageContainer">
          <!-- 加载状态 -->
          <div v-if="loading" class="loading-message">
            <el-skeleton :rows="3" animated />
          </div>
          
          <!-- 统计卡片消息 -->
          <div v-else class="message assistant stats">
            <div class="message-avatar">
              <el-avatar :size="36" src="/ai-avatar.png" />
            </div>
            <div class="message-content stats">
              <!-- 统计卡片 -->
              <div class="stats-section full-width">
                <div class="stats-grid">
                  <StatisticCard
                    v-for="stat in statistics"
                    :key="stat.label"
                    v-bind="stat"
                  />
                </div>
              </div>
              
              <!-- 图表 -->
              <div class="charts-section">
                <div class="stats-section">
                  <ChartCard
                    title="任务完成趋势"
                    :option="taskTrendOption"
                    :showTimeRange="true"
                  />
                </div>
                <div class="stats-section">
                  <ChartCard
                    title="任务类型分布"
                    :option="taskTypeOption"
                  />
                </div>
              </div>

              <!-- 最近活动 -->
              <div class="stats-section full-width">
                <TimelineCard
                  title="最近活动"
                  :activities="recentActivities"
                />
                
                <div class="ai-summary">
                  根据当前数据分析，本周任务完成率达到85%，较上周提升5个百分点。
                  待处理任务8个，建议优先关注系统性能优化相关任务。
                </div>

                <div class="todo-list">
                  <h4>建议接下来的工作：</h4>
                  <ol>
                    <li>完成系统性能优化任务</li>
                    <li>评审新功能原型设计</li>
                    <li>更新测试用例文档</li>
                  </ol>
                </div>
              </div>
            </div>
          </div>

          <!-- 其他消息 -->
          <div v-for="(msg, index) in messages" :key="index" 
               :class="['message', msg.type === 'user' ? 'user' : 'assistant']">
            <div class="message-avatar">
              <el-avatar :size="36" :src="msg.type === 'user' ? 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png' : '/ai-avatar.png'" />
            </div>
            <div class="message-content">
              <p>{{ msg.content }}</p>
            </div>
            <span class="message-time">{{ msg.time }}</span>
          </div>
        </div>

        <div class="chat-input">
          <el-input
            v-model="message"
            placeholder="输入您的问题..."
            :autosize="{ minRows: 1, maxRows: 4 }"
            type="textarea"
            @keyup.enter.prevent="sendMessage"
          />
          <el-button type="primary" @click="sendMessage" :disabled="!message.trim()">
            发送
            <el-icon class="send-icon"><Position /></el-icon>
          </el-button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import dayjs from 'dayjs'
import { 
  ChatLineRound, 
  DataLine, 
  List, 
  Setting, 
  Bell,
  Position,
  Calendar,
  Check,
  Warning,
  Monitor
} from '@element-plus/icons-vue'
import StatisticCard from './components/StatisticCard.vue'
import ChartCard from './components/ChartCard.vue'
import TimelineCard from './components/TimelineCard.vue'

const loading = ref(true)
const message = ref('')
const messages = ref([
  { type: 'assistant', content: '你好！我是你的智能助手，有什么我可以帮你的吗？', time: dayjs().format('YYYY-MM-DD HH:mm:ss') },
  { type: 'user', content: '你好！', time: dayjs().format('YYYY-MM-DD HH:mm:ss') }
])

// 图表配置
const taskTrendOption = {
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: ['12-30', '12-31', '01-01', '01-02', '01-03', '01-04', '01-05'],
    axisLine: {
      lineStyle: {
        color: '#909399'
      }
    },
    axisLabel: {
      color: '#606266'
    }
  },
  yAxis: {
    type: 'value',
    axisLine: {
      lineStyle: {
        color: '#909399'
      }
    },
    axisLabel: {
      color: '#606266'
    },
    splitLine: {
      lineStyle: {
        color: '#f0f0f0'
      }
    }
  },
  series: [{
    name: '完成任务数',
    type: 'line',
    smooth: true,
    data: [150, 230, 224, 218, 135, 147, 260],
    itemStyle: {
      color: '#409EFF'
    },
    areaStyle: {
      color: {
        type: 'linear',
        x: 0,
        y: 0,
        x2: 0,
        y2: 1,
        colorStops: [{
          offset: 0,
          color: 'rgba(64,158,255,0.2)'
        }, {
          offset: 1,
          color: 'rgba(64,158,255,0)'
        }]
      }
    }
  }]
}

const taskTypeOption = {
  tooltip: {
    trigger: 'item',
    formatter: '{b}: {c} ({d}%)'
  },
  legend: {
    orient: 'vertical',
    right: 10,
    top: 'center',
    textStyle: {
      color: '#606266'
    }
  },
  series: [
    {
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 20,
          fontWeight: 'bold'
        }
      },
      labelLine: {
        show: false
      },
      data: [
        { value: 1048, name: '开发任务', itemStyle: { color: '#409EFF' } },
        { value: 735, name: '设计任务', itemStyle: { color: '#67C23A' } },
        { value: 580, name: '测试任务', itemStyle: { color: '#E6A23C' } },
        { value: 484, name: '运维任务', itemStyle: { color: '#F56C6C' } }
      ]
    }
  ]
}

// 最近活动数据
const recentActivities = [
  {
    content: '完成了任务 "更新用户界面"',
    timestamp: '2024-01-05 10:00',
    type: 'success',
    color: '#52c41a'
  },
  {
    content: '收到新的任务 "优化系统性能"',
    timestamp: '2024-01-05 09:30',
    type: 'warning',
    color: '#faad14'
  },
  {
    content: '部署了新版本',
    timestamp: '2024-01-05 09:00',
    type: 'primary',
    color: '#1890ff'
  }
]

const statistics = [
  {
    label: '今日任务',
    value: 12,
    trend: 15,
    icon: 'Calendar',
    iconBg: '#e6f4ff',
    iconColor: '#1890ff'
  },
  {
    label: '完成率',
    value: '85%',
    trend: 5,
    icon: 'Check',
    iconBg: '#f6ffed',
    iconColor: '#52c41a'
  },
  {
    label: '待处理',
    value: 8,
    trend: -10,
    icon: 'Warning',
    iconBg: '#fff2e8',
    iconColor: '#fa8c16'
  },
  {
    label: '系统状态',
    value: '正常',
    trend: 0,
    icon: 'Monitor',
    iconBg: '#f9f0ff',
    iconColor: '#722ed1'
  }
]

const sendMessage = () => {
  if (!message.value.trim()) return
  
  const now = dayjs()
  messages.value.push({
    type: 'user',
    content: message.value,
    time: now.format('YYYY-MM-DD HH:mm:ss')
  })
  
  message.value = ''
}

// 模拟加载效果
onMounted(() => {
  setTimeout(() => {
    loading.value = false
  }, 2000)
})
</script>

<style scoped>
.app-container {
  display: flex;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 240px;
  background-color: #001529;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.logo {
  height: 60px;
  padding: 0 24px;
  background: #002140;
  display: flex;
  align-items: center;
}

.logo h2 {
  color: white;
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.menu {
  flex: 1;
  padding: 12px 0;
}

.menu-item {
  height: 50px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  color: rgba(255, 255, 255, 0.65);
  cursor: pointer;
  transition: all 0.3s;
}

.menu-item:hover {
  background-color: #002140;
  color: white;
}

.menu-item.active {
  background-color: #1890ff;
  color: white;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  min-width: 0; /* 防止子元素溢出 */
}

.header {
  height: 60px;
  background: white;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0,21,41,0.08);
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #1f2f3d;
}

.separator {
  color: #909399;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.chat {
  flex: 1;
  margin: 24px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  padding: 32px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 32px;
  background: #FAFAFA;
}

.message {
  display: flex;
  gap: 16px;
  max-width: 85%;
  position: relative;
  padding-bottom: 24px;
}

.message.assistant {
  align-self: flex-start;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.assistant.stats {
  max-width: 100%;
  width: 100%;
}

.message-avatar {
  flex-shrink: 0;
}

.message-avatar :deep(.el-avatar) {
  border: 2px solid white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.message-content {
  background: white;
  padding: 16px 20px;
  border-radius: 16px;
  position: relative;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  color: #1f2f3d;
  line-height: 1.6;
  font-size: 14px;
}

.message.assistant .message-content {
  border-bottom-left-radius: 4px;
}

.message.user .message-content {
  background: #4B5563;
  color: white;
  border-bottom-right-radius: 4px;
}

.message-content.stats {
  background: transparent;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 24px;
  box-shadow: none;
}

.message-time {
  position: absolute;
  bottom: 0;
  font-size: 12px;
  color: #9CA3AF;
  right: 0;
  left: 52px;
}

.message.user .message-time {
  text-align: right;
  right: 52px;
  left: 0;
}

.chat-input {
  padding: 24px 32px;
  background: white;
  border-top: 1px solid #E5E7EB;
  display: flex;
  gap: 16px;
  align-items: flex-end;
}

:deep(.el-input__wrapper) {
  box-shadow: none !important;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 8px 16px;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:focus-within) {
  border-color: #4B5563;
  box-shadow: 0 0 0 2px rgba(75, 85, 99, 0.1) !important;
}

:deep(.el-textarea__inner) {
  min-height: 24px !important;
  max-height: 120px;
  padding: 0;
  font-size: 14px;
  line-height: 1.6;
  resize: none;
}

:deep(.el-button) {
  border-radius: 12px;
  padding: 12px 24px;
  font-weight: 500;
  transition: all 0.3s ease;
  height: auto;
}

:deep(.el-button:not(:disabled):hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* 滚动条样式 */
.chat-messages::-webkit-scrollbar {
  width: 8px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #E5E7EB;
  border-radius: 4px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #D1D5DB;
}

/* 统计卡片样式 */
.stats-section {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  height: 100%;
}

.stats-section .chart-container {
  height: calc(100% - 40px); /* 减去标题的高度 */
  width: 100%;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  height: 100px;
  margin-bottom: 24px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  height: 360px;
}

.charts-section {
  margin-top: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.ai-summary {
  background: #F3F4F6;
  padding: 20px;
  border-radius: 12px;
  margin-top: 20px;
  color: #1f2f3d;
  line-height: 1.6;
  font-size: 14px;
}

.todo-list {
  background: #F3F4F6;
  padding: 20px;
  border-radius: 12px;
  margin-top: 20px;
}

.todo-list h4 {
  margin: 0 0 16px 0;
  color: #1f2f3d;
  font-size: 14px;
  font-weight: 600;
}

.todo-list ol {
  margin: 0;
  padding-left: 24px;
}

.todo-list li {
  color: #1f2f3d;
  line-height: 1.6;
  margin-bottom: 12px;
  font-size: 14px;
}

.todo-list li:last-child {
  margin-bottom: 0;
}
</style>