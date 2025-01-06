<template>
  <div class="message" :class="{ 'message-ai': isAI, 'message-user': !isAI }">
    <div class="message-avatar">
      <el-avatar 
        :size="40" 
        :src="isAI ? '/assets/ai-avatar.svg' : '/assets/user-avatar.svg'"
      />
    </div>
    <div class="message-content">
      <div class="message-info">
        <span class="message-name">{{ isAI ? 'Claude' : 'Zapz' }}</span>
        <span class="message-time">{{ formatTime(time) }}</span>
      </div>
      <div v-if="status === 'thinking'" class="thinking-indicator">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>正在思考...</span>
      </div>
      <div v-else-if="status === 'using_tool'" class="tool-indicator">
        <el-icon class="is-loading"><Tools /></el-icon>
        <span>正在使用工具...</span>
      </div>
      <div v-else>
        <div v-if="!isAI" class="message-text">{{ content }}</div>
        <div v-else class="message-markdown" v-html="markdownContent"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { Loading, Tools } from '@element-plus/icons-vue'

const props = defineProps({
  content: {
    type: String,
    required: true
  },
  isAI: {
    type: Boolean,
    default: false
  },
  time: {
    type: Date,
    default: () => new Date()
  },
  status: {
    type: String,
    default: 'done'
  }
})

const markdownContent = computed(() => {
  if (!props.isAI) return props.content
  return DOMPurify.sanitize(marked(props.content))
})

const formatTime = (date) => {
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).format(date)
}
</script>

<style scoped>
.message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  align-items: flex-start;
  width: 100%;
  max-width: 80%;
}

.message-ai {
  margin-right: auto;
  flex-direction: row;
}

.message-user {
  margin-left: auto;
  justify-content: flex-start;
  flex-direction: row-reverse;
}

.message-avatar {
  display: flex;
  align-items: center;
  height: 100%;
  min-height: 40px;
  margin-top: 8px;
}

.message-content {
  max-width: 800px;
  margin-top: 8px;
  text-align: left;
}

.message-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 12px;
  color: #999;
}

.message-name {
  font-weight: 500;
  color: #1f2f3d;
}

.message-time {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}

.message-text, .message-markdown {
  display: inline-block;
  max-width: 100%;
  padding: 8px 12px;
  border-radius: 12px;
  line-height: 1.5;
  word-wrap: break-word;
  white-space: pre-wrap;
  font-size: 14px;
}

.message-ai .message-text,
.message-ai .message-markdown {
  background-color: #f5f7fa;
  color: #303133;
}

.message-user .message-text {
  background-color: var(--el-color-primary);
  color: #fff;
}

.thinking-indicator,
.tool-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 12px;
  background-color: #f5f7fa;
  color: #666;
  font-size: 14px;
}

.tool-indicator {
  background-color: #f0f9eb;
  color: #67c23a;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.is-loading {
  animation: spin 1s linear infinite;
}
</style> 