import OpenAI from 'openai';
import { functions_tools } from './functionDescription';

// 从 localStorage 获取设置
const getSettings = () => {
  const settings = JSON.parse(localStorage.getItem('aiSettings') || '{}')
  return {
    baseURL: settings.baseURL || 'https://api.deepseek.com',
    apiKey: settings.apiKey || '',
    model: settings.model || 'deepseek-chat'
  }
}

// 初始化 OpenAI 实例
const initOpenAI = () => {
  const { baseURL, apiKey } = getSettings()
  return new OpenAI({
    baseURL,
    apiKey,
    dangerouslyAllowBrowser: true
  })
}

const openai = initOpenAI()

// 动态获取模型
const getModel = () => {
  return getSettings().model
}

/**
 * 创建聊天完成请求
 * @param {Object} options - 请求选项
 * @param {Array} options.messages - 消息历史记录
 * @param {boolean} [options.stream=true] - 是否使用流式响应
 * @param {number} [options.temperature=0.0] - 温度参数
 * @param {Array} [options.tools] - 工具定义
 * @param {string} [options.tool_choice='auto'] - 工具选择模式
 * @returns {Promise} - 返回 OpenAI API 响应
 */
export const createChatCompletion = async ({
  messages,
  stream = true,
  temperature = 0.0,
  tools = functions_tools,
  tool_choice = 'auto'
}) => {
  try {
    return await openai.chat.completions.create({
      messages,
      model: getModel(),
      temperature,
      tools,
      tool_choice,
      stream
    });
  } catch (error) {
    console.error('[ERROR] 创建聊天完成请求失败:', error);
    throw error;
  }
}
