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
        :component-type="message.componentType"
        :component-data="message.componentData"
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
const messages = ref([
  // 示例消息
  {
    content: '您好Zapz，您的销售数据如下',
    isAI: true,
    time: new Date(),
    status: 'done'
  },
  {
    content: '',
    isAI: true,
    time: new Date(),
    status: 'done',
    componentType: 'ChartCard',
    componentData: {
      description: '昨日西风凋碧树，独上高楼，望尽天涯路。衣带渐宽终不悔，为伊消得人憔悴。众里寻他千百度，蓦然回首，那人却在，灯火阑珊处。',
      option: {
        title: {
          text: '近期销售趋势',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: ['1月', '2月', '3月', '4月']
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            name: '销售额',
            type: 'line',
            data: [120, 200, 150, 300],
            smooth: true,
            itemStyle: {
              color: '#409EFF'
            }
          }
        ]
      }
    }
  }
])

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
    console.log('[DEBUG] 2 看一下:', messages.value)
    // 处理AI响应
    let isFirstChunk = true;
    for await (const chunk of sendMessageToAIStream(messages.value)) {
      if (isFirstChunk) {
        aiMessage.status = chunk.status;
        isFirstChunk = false;
      }

      if(chunk.status === 'tool_result') {
        messages.value = messages.value.map((msg, index) => {
          // 如果是最后一条消息，则更新其内容和状态
          // 这里与AI交互是流式输出，所以动态的更新最后一条消息和状态，以便于UI的更新
          if (index === messages.value.length - 1) {
            return {
              content: '',
              status: 'done',
              isAI: true,
              time: new Date(),
              componentType: chunk.componentType,
              componentData: {
                weatherData: JSON.parse(chunk.content)
              }
            }
          }
          return msg
        })

      }
      
      // 使用 Vue 的响应式更新方式
      messages.value = messages.value.map((msg, index) => {
        // 如果是最后一条消息，则更新其内容和状态
        // 这里与AI交互是流式输出，所以动态的更新最后一条消息和状态，以便于UI的更新
        if (index === messages.value.length - 1) {
          return {
            ...msg,
            content: chunk.status === 'responding' ? msg.content + chunk.content : msg.content,
            status: chunk.status
          }
        }
        return msg
      })

      // 确保 DOM 更新
      await nextTick()
      scrollToBottom()
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
  border-radius: 8px;
}

.chat-container > * {
  margin-bottom: 16px;
}

.message-ai .card-container {
  width: 100%;
  max-width: 600px;
  margin: 8px 0;
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
