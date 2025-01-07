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
        <div v-else>
          <component
            v-if="componentType"
            :is="getComponent(componentType)"
            v-bind="componentData"
          />
          <div v-else class="message-markdown markdown-body" v-html="parsedContent"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onUnmounted } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import 'github-markdown-css/github-markdown.css'
import { Loading, Tools } from '@element-plus/icons-vue'
import ChartCard from './ChartCard.vue'
import StatisticCard from './StatisticCard.vue'
import TimelineCard from './TimelineCard.vue'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

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
  },
  componentType: {
    type: String,
    default: ''
  },
  componentData: {
    type: Object,
    default: () => ({})
  }
})

const displayContent = ref('')
const currentContent = computed(() => props.content)
let typingTimeout = null

// 配置 marked
marked.setOptions({
  gfm: true,
  breaks: true,
  sanitize: false,
  highlight: function(code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext'
    return hljs.highlight(code, { language }).value
  }
})

// 添加 markdown 解析
const parsedContent = computed(() => {
  if (!props.isAI || props.componentType) return displayContent.value
  return DOMPurify.sanitize(marked.parse(displayContent.value))
})

watch(currentContent, (newVal) => {
  // 清除之前的定时器
  if (typingTimeout) {
    clearTimeout(typingTimeout)
  }

  // 如果内容变短了（比如清空），直接更新
  if (newVal.length < displayContent.value.length) {
    displayContent.value = newVal
    return
  }

  // 流式显示新内容
  const newChars = newVal.slice(displayContent.value.length)
  let index = 0

  const typeNextChar = () => {
    if (index < newChars.length) {
      displayContent.value += newChars[index]
      index++
      typingTimeout = setTimeout(typeNextChar, 20)
    }
  }

  typeNextChar()
}, { immediate: true })

// 组件卸载时清除定时器
onUnmounted(() => {
  if (typingTimeout) {
    clearTimeout(typingTimeout)
  }
})

const formatTime = (date) => {
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).format(date)
}

const componentsMap = {
  'StatisticCard': StatisticCard,
  'ChartCard': ChartCard,
  'TimelineCard': TimelineCard
}

const getComponent = (type) => {
  return componentsMap[type] || null
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
  text-align: right;
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
  /*white-space: pre-wrap;*/
  font-size: 14px;
}
.message-markdown
{
  text-align: left;
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

/* 覆盖github-markdown-css的一些样式 */
:deep(.markdown-body) {
  font-size: 14px;
  line-height: 1.6;
  word-wrap: break-word;
}

:deep(.markdown-body pre) {
  background-color: #f6f8fa;
  padding: 16px;
  border-radius: 6px;
  overflow: auto;
}

:deep(.markdown-body code) {
  font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace;
  font-size: 85%;
  background-color: rgba(175, 184, 193, 0.2);
  padding: 0.2em 0.4em;
  border-radius: 6px;
}

:deep(.markdown-body table) {
  border-collapse: collapse;
  margin: 16px 0;
}

:deep(.markdown-body th),
:deep(.markdown-body td) {
  padding: 6px 13px;
  border: 1px solid #dfe2e5;
}

:deep(.markdown-body blockquote) {
  padding: 0 1em;
  color: #57606a;
  border-left: 0.25em solid #dfe2e5;
  margin: 0;
}
</style> 