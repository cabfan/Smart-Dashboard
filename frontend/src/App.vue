<template>
  <el-container class="app-container" @keydown.enter="focusInput">
    <!-- 侧边栏 -->
    <el-aside width="260px" class="sidebar">
      <div class="logo">
        <el-icon class="logo-icon" :size="32"><Monitor /></el-icon>
        <span class="logo-text">Smart Dashboard</span>
      </div>
      <el-menu
        default-active="1"
        class="sidebar-menu"
        background-color="var(--menu-bg)"
        text-color="#fff"
        active-text-color="var(--primary-color)"
      >
        <el-menu-item index="1">
          <el-icon><Monitor /></el-icon>
          <span>数据概览</span>
        </el-menu-item>
        <el-menu-item index="2">
          <el-icon><ChatLineRound /></el-icon>
          <span>AI 助手</span>
        </el-menu-item>
        <el-menu-item index="3">
          <el-icon><Document /></el-icon>
          <span>任务管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="main-container">
      <!-- 头部 -->
      <el-header class="header">
        <div class="breadcrumb">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>首页</el-breadcrumb-item>
            <el-breadcrumb-item>AI 助手</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-actions">
          <div class="notification-icon">
            <el-icon :size="20" color="#666"><Bell /></el-icon>
            <span class="notification-badge">3</span>
          </div>
          <el-dropdown>
            <el-avatar class="avatar" :size="32" src="/assets/user-avatar.svg" />
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人信息</el-dropdown-item>
                <el-dropdown-item>设置</el-dropdown-item>
                <el-dropdown-item divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 聊天主界面 -->
      <el-main class="chat-container">
        <div class="chat-wrapper">
          <!-- 聊天历史记录 -->
          <div class="chat-messages" ref="messagesContainer">
            <ChatMessage
              v-for="(msg, index) in messages"
              :key="index"
              :content="msg.content"
              :isAI="msg.isAI"
              :time="msg.time"
              :status="msg.status"
            />
          </div>
          
          <!-- 输入框区域 -->
          <div class="chat-input-wrapper">
            <div class="chat-input-container">
              <div class="input-with-button">
                <el-input
                  ref="messageInputRef"
                  v-model="messageInput"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入消息..."
                  @keydown.enter.exact.prevent="sendMessage"
                  :disabled="isLoading"
                />
                <el-button
                  class="send-button"
                  type="primary"
                  :loading="isLoading"
                  @click="sendMessage"
                  :style="{ position: 'absolute', right: '12px', bottom: '12px' }"
                >
                  发送
                </el-button>
              </div>
            </div>
          </div>
          
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, onUnmounted } from 'vue'
import ChatMessage from './components/ChatMessage.vue'
import { Bell, Monitor, ChatLineRound, Document, Position } from '@element-plus/icons-vue'
import { sendMessageToAIStream } from './utils/openai'

const messages = ref([])
const messageInput = ref('')
const isLoading = ref(false)

// 获取消息容器的引用
const messagesContainer = ref(null)

// 自动滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 监听messages变化
watch(messages, () => {
  scrollToBottom()
}, { deep: true })

// 初始化时也滚动到底部
onMounted(() => {
  scrollToBottom()
})

// 初始化欢迎消息
const initWelcomeMessage = () => {
  messages.value.push({
    content: '您好！我是您的 AI 助手，有什么可以帮您的吗？',
    isAI: true,
    time: new Date(),
    isStreaming: false
  })
}

onMounted(() => {
  initWelcomeMessage()
})

const sendMessage = async () => {
  if (!messageInput.value.trim() || isLoading.value) return;
  
  const userMessage = messageInput.value;
  messages.value.push({
    content: userMessage,
    isAI: false,
    time: new Date(),
    status: 'done'  // 用户消息状态始终为done
  });
  
  messageInput.value = '';
  isLoading.value = true;
  
  try {
    const aiMessage = {
      content: '',
      isAI: true,
      time: new Date(),
      status: 'thinking',  // 初始状态为thinking
      id: Date.now()
    }
    messages.value.push(aiMessage)

    const stream = sendMessageToAIStream(userMessage, messages.value)
    for await (const response of stream) {
      const index = messages.value.findIndex(m => m.id === aiMessage.id)
      if (index !== -1) {
        // 更新消息状态和内容
        messages.value[index] = {
          ...messages.value[index],
          status: response.status,
          content: response.content ? 
            messages.value[index].content + response.content : 
            messages.value[index].content
        }
      }
    }
  } catch (error) {
    console.error('Error:', error);
    messages.value.push({
      content: '抱歉，AI 助手暂时无法响应，请稍后再试。',
      isAI: true,
      time: new Date(),
      status: 'error'
    });
  } finally {
    isLoading.value = false
  }
};

const messageInputRef = ref(null)

const focusInput = () => {
  if (!isLoading.value) {
    messageInputRef.value?.focus()
  }
}

// 添加全局事件监听器
onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
})

// 移除全局事件监听器
onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})

const handleGlobalKeydown = (event) => {
  // 检查是否按下了回车键
  if (event.key === 'Enter' && !event.ctrlKey && !event.shiftKey && !event.metaKey) {
    // 如果当前焦点不在输入框内
    if (document.activeElement !== messageInputRef.value?.textarea) {
      event.preventDefault()
      focusInput()
    }
  }
}

</script>

<style scoped>
/* 添加全局样式 */
:global(body) {
  margin: 0;
  padding: 0;
  overflow: hidden;  /* 隐藏body的滚动条 */
  height: 100vh;
}

.app-container {
  width: 100%;
  height: 100vh;
  overflow: hidden;  /* 隐藏容器滚动条 */
}

.sidebar {
  background-color: #001529;
  color: #fff;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  border-right: 1px solid rgba(0, 0, 0, 0.1);
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  background: #002140;
}

.logo-icon {
  color: #1890ff;
  margin-right: 8px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
}

.main-container {
  margin-left: 260px;
  height: 100vh;
  overflow: hidden;  /* 隐藏主容器滚动条 */
  background: #fff;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}

.notification-icon {
  position: relative;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.notification-icon:hover {
  background-color: #f5f7fa;
}

.notification-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  background-color: #f56c6c;
  color: white;
  font-size: 12px;
  min-width: 16px;
  height: 16px;
  line-height: 16px;
  text-align: center;
  border-radius: 8px;
  padding: 0 4px;
}

.avatar {
  cursor: pointer;
  transition: transform 0.2s;
}

.avatar:hover {
  transform: scale(1.1);
}

.chat-container {
  padding: 0;
  height: calc(100vh - 60px);
  position: relative;
  overflow: hidden;  /* 隐藏聊天容器滚动条 */
}

.chat-wrapper {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;  /* 隐藏wrapper滚动条 */
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  margin-bottom: 16px;
  scroll-behavior: smooth;  /* 添加平滑滚动效果 */
}

.message {
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 8px;
  max-width: 70%;
}

.user-message {
  margin-left: auto;
  background-color: #e6f7ff;
}

.ai-message {
  margin-right: auto;
  background-color: #f5f5f5;
}

.message-content {
  word-wrap: break-word;
  white-space: pre-wrap;
}

.message-time {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.chat-input-wrapper {
  border-top: 1px solid #f0f0f0;
  padding: 24px;
  background: #fff;
}

.chat-input-container {
  position: relative;
  max-width: 768px;
  margin: 0 auto;
  padding-right: 100px;
}

.send-button {
  position: absolute;
  right: 0;
  bottom: 8px;
  width: 80px;
  height: 36px;
  padding: 8px 12px;
  transition: none;
}

:deep(.el-button.is-loading) {
  width: 80px;
  height: 36px;
  padding: 8px 12px;
}

:deep(.el-menu) {
  border-right: none;
}

:deep(.el-menu-item) {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #fff !important;
}

:deep(.el-menu-item:hover) {
  background-color: #1890ff !important;
}

:deep(.el-menu-item.is-active) {
  background-color: #1890ff !important;
  color: #fff !important;
}

:deep(.el-textarea__inner) {
  padding-right: 100px;
  resize: none;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  min-height: 100px;
}
</style>