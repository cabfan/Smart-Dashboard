<template>
  <div class="chat-container">
    <div class="chat-messages" ref="messagesContainer">
      <div v-for="(message, index) in messages" :key="index" 
           :class="['message', message.isAI ? 'ai' : 'user']">
        <div class="message-content">
          {{ message.content }}
        </div>
        <div class="message-time">
          {{ new Date(message.time).toLocaleTimeString() }}
        </div>
      </div>
    </div>
    
    <div class="chat-input">
      <el-input
        v-model="inputMessage"
        type="textarea"
        :rows="3"
        placeholder="输入消息..."
        @keyup.enter.native.exact="sendMessage"
      />
      <el-button type="primary" @click="sendMessage" :loading="isLoading">
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { functions_tools } from '../utils/functionDescription'

const ws = ref(null)
const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)

// 连接WebSocket
const connectWebSocket = () => {
  ws.value = new WebSocket('ws://localhost:3001/ws')
  
  ws.value.onopen = () => {
    console.log('WebSocket connected')
    messages.value.push({
      content: '您的数据助手已上线，今天想查询点什么？',
      isAI: true,
      time: new Date()
    })
  }
  
  ws.value.onmessage = (event) => {
    const data = JSON.parse(event.data)
    
    if (data.type === 'stream') {
      let content = data.content;
      try {
        // 尝试解析 JSON 内容
        const jsonData = JSON.parse(data.content);
        if (jsonData.city) {
          // 格式化天气信息
          content = `${jsonData.message}\n温度：${jsonData.temperature}\n天气：${jsonData.weather}\n湿度：${jsonData.humidity}\n风力：${jsonData.wind}`;
        } else if (jsonData.timestamp) {
          // 格式化时间信息
          content = `当前时间是：${jsonData.formatted}`;
        }
      } catch (e) {
        // 如果不是 JSON，直接使用原内容
        content = data.content;
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
    console.log('WebSocket disconnected')
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
  
  isLoading.value = true
  try {
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
})

// 组件卸载时关闭WebSocket
onUnmounted(() => {
  if (ws.value) {
    ws.value.close()
  }
})
</script>

<style scoped>
.chat-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
  margin-bottom: 20px;
}

.message {
  margin-bottom: 12px;
  max-width: 80%;
}

.message.user {
  margin-left: auto;
}

.message-content {
  padding: 10px 16px;
  border-radius: 8px;
  background: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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

.chat-input {
  display: flex;
  gap: 12px;
}

.chat-input .el-input {
  flex: 1;
}
</style> 