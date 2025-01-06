<template>
  <div class="dashboard-container"  @keydown.enter="focusInput">
    <!-- 聊天容器 -->
    <div ref="messagesContainer" class="chat-container">
      <ChatMessage
        v-for="(message, index) in messages"
        :key="index"
        :content="message.content"
        :isAI="message.isAI"
        :time="message.time"
        :status="message.status"
      />
    </div>

    <!-- 输入框 -->
    <div class="chat-input-container">
      <el-input
        ref="messageInputRef"
        v-model="messageInput"
        type="textarea"
        :rows="3"
        placeholder="请输入消息..."
        @keydown.enter.exact.prevent="sendMessage"
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
import ChatMessage from '../components/ChatMessage.vue'
import { sendMessageToAIStream } from '../utils/openai'
import { Promotion, Loading } from '@element-plus/icons-vue'

// 消息列表
const messages = ref([])
const messageInput = ref('')
const isLoading = ref(false)
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

const messageInputRef = ref(null)
const focusInput = () => {
  if (!isLoading.value) {
    messageInputRef.value?.focus()
  }
}

// 全局事件监听器 监听回车键 如果当前焦点不在输入框内 则聚焦输入框
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

// 初始化欢迎消息
const initWelcomeMessage = () => {
  messages.value.push({
    content: '您好 Zapz！我是您的 AI 助手，有什么可以帮您的吗？',
    isAI: true,
    time: new Date(),
    status: 'done'
  })
}

// 在 setup 中添加 isSending 状态
const isSending = ref(false)

// 发送消息
const sendMessage = async () => {
  if (!messageInput.value.trim() || isLoading.value) return;

  // 添加防抖保护
  if (isSending.value) return;
  isSending.value = true;
  isLoading.value = true;

  try {
    const userMessage = messageInput.value;
    messages.value.push({
      content: userMessage,
      isAI: false,
      time: new Date(),
      status: 'done'
    });

    // 清空输入框
    messageInput.value = '';

    // 添加AI消息占位符
    const aiMessage = {
      content: '',
      isAI: true,
      time: new Date(),
      status: 'thinking'
    };
    messages.value.push(aiMessage);
    console.log('[DEBUG] 历史消息:', messages.value);
    // 处理AI响应
    let isFirstChunk = true;
    for await (const chunk of sendMessageToAIStream(userMessage, messages.value)) {
      if (isFirstChunk) {
        aiMessage.status = chunk.status;
        isFirstChunk = false;
      }

      // 更新最后一条消息
      const lastMessage = messages.value[messages.value.length - 1];
      if (chunk.status === 'responding') {
        lastMessage.content += chunk.content;
      } else {
        lastMessage.status = chunk.status;
      }
    }
  } catch (error) {
    console.error('发送消息失败:', error);
    // 更新最后一条消息状态为错误
    const lastMessage = messages.value[messages.value.length - 1];
    lastMessage.status = 'error';
    lastMessage.content = '抱歉，消息发送失败，请重试。';
  } finally {
    isSending.value = false;
    isLoading.value = false;
  }
};

// 添加全局事件监听器
onMounted(() => {
    initWelcomeMessage()
    scrollToBottom()
    window.addEventListener('keydown', handleGlobalKeydown)
})

// 移除全局事件监听器
onUnmounted(() => {
    window.removeEventListener('keydown', handleGlobalKeydown)
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
  margin-bottom: 20px;
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

/* 确保按钮内容居中 */
:deep(.el-button > span) {
  margin-left: 8px;
}

</style>
