<template>
  <el-container class="app-container">
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
          <div class="chat-messages">
            <div v-for="(msg, index) in messages" :key="index" 
                 :class="['message', msg.isAI ? 'ai-message' : 'user-message']">
              <div class="message-content">
                {{ msg.content }}
              </div>
              <div class="message-time">
                {{ formatTime(msg.time) }}
              </div>
            </div>
          </div>
          
          <!-- 输入框区域 -->
          <div class="chat-input-wrapper">
            <div class="chat-input-container">
              <el-input
                v-model="messageInput"
                type="textarea"
                :rows="3"
                placeholder="请输入消息..."
                @keydown.enter.exact.prevent="sendMessage"
              />
              <el-button
                class="send-button"
                type="primary"
                :loading="isLoading"
                @click="sendMessage"
              >
                发送
              </el-button>
            </div>
          </div>
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import ChatMessage from './components/ChatMessage.vue'
import { Bell, Monitor, ChatLineRound, Document, Position } from '@element-plus/icons-vue'
import { sendMessageToAI } from './utils/openai'

const messages = ref([])
const messageInput = ref('')
const isLoading = ref(false)

// 初始化欢迎消息
const initWelcomeMessage = () => {
  messages.value.push({
    content: '您好！我是您的 AI 助手，有什么可以帮您的吗？',
    isAI: true,
    time: new Date()
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
    time: new Date()
  });
  
  messageInput.value = '';
  isLoading.value = true;
  
  try {
    const response = await sendMessageToAI(userMessage, messages.value);
    
    messages.value.push({
      content: response,
      isAI: true,
      time: new Date()
    });
    
  } catch (error) {
    console.error('Error:', error);
    messages.value.push({
      content: '抱歉，AI 助手暂时无法响应，请稍后再试。',
      isAI: true,
      time: new Date()
    });
  } finally {
    isLoading.value = false;
  }
};

// 添加时间格式化函数
const formatTime = (date) => {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).format(new Date(date));
};
</script>

<style scoped>
.app-container {
  width: 100%;
  height: 100vh;
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
  min-height: 100vh;
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
}

.chat-wrapper {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
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