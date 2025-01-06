import OpenAI from 'openai';
// 从functionDescription导入工具定义
import { functions_tools } from './functionDescription';

const openai = new OpenAI({
  baseURL: 'https://api.deepseek.com',
  apiKey: 'sk-e09b1c2850754858b41d8579766b60e2',
  dangerouslyAllowBrowser: true
});


/**
 * 判断是否需要调用工具
 * @param {string} message - 用户最新消息
 * @returns {Promise<Object>} - 返回AI判断结果
 */
const checkToolUsage = async (message) => {
  const startTime = performance.now()  // 记录开始时间
  const systemPrompt = `
  请分析用户的消息内容，判断是否需要调用工具。
  如果需要调用工具，请返回以下JSON格式：
  {
    "need_tool": true,
    "tool_name": "工具名称"
  }
  如果不需要调用工具，请返回：
  {
    "need_tool": false
  }
  当前可用工具：
  - get_weather: 获取天气信息，需要同时满足以下条件：
    1. 用户明确表示要查询天气信息
    2. 用户提供了有效的地点信息
  `;

  try {
    const response = await openai.chat.completions.create({
      model: "deepseek-chat",
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: message }
      ],
      response_format: { type: "json_object" }
    });

    const endTime = performance.now()  // 记录结束时间
    console.log(`[PERF] 工具判断耗时: ${(endTime - startTime).toFixed(2)}ms`)
    return JSON.parse(response.choices[0].message.content);
  } catch (error) {
    console.error('判断工具使用时出错:', error);
    return { need_tool: false };
  }
};



// 模拟天气API
const mockWeatherAPI = async (location) => {
  console.log('[DEBUG] 调用模拟天气API，位置:', location);
  return `${location} 当前天气：24℃，晴`;
};

/**
 * 处理常规对话（流式版本）
 * @param {Array} messages - 完整的消息历史记录
 * @returns {AsyncGenerator<string>} - 返回AI的响应内容流
 */
const handleRegularConversationStream = async function* (messages) {
  const startTime = performance.now()  // 记录开始时间
  const stream = await openai.chat.completions.create({
    messages,
    model: 'deepseek-chat',
    temperature: 1.0,
    stream: true
  });

  let firstChunkTime = null
  for await (const chunk of stream) {
    if (!firstChunkTime) {
      firstChunkTime = performance.now()
      console.log(`[PERF] 首字节响应时间: ${(firstChunkTime - startTime).toFixed(2)}ms`)
    }
    
    const content = chunk.choices[0]?.delta?.content || '';
    if (content) {
      yield content;
    }
  }

  const endTime = performance.now()  // 记录结束时间
  console.log(`[PERF] 对话总耗时: ${(endTime - startTime).toFixed(2)}ms`)
};

/**
 * 处理工具调用
 * @param {Object} assistantMessage - AI助手的消息对象
 * @param {Array} messages - 完整的消息历史记录
 * @returns {AsyncGenerator<string>} - 返回处理后的最终响应内容流
 */
const handleToolCall = async function* (assistantMessage, messages) {
  const startTime = performance.now()  // 记录开始时间
  console.log('[DEBUG] 检测到工具调用:', assistantMessage.tool_calls);

  // 收集所有工具调用结果
  const toolResponses = await Promise.all(
    assistantMessage.tool_calls.map(async (toolCall) => {
      const functionName = toolCall.function.name;
      const functionArgs = JSON.parse(toolCall.function.arguments);

      console.log('[DEBUG] 工具调用详情:', { functionName, functionArgs });

      let result;
      switch (functionName) {
        case 'get_weather':
          result = await mockWeatherAPI(functionArgs.location);
          break;
        default:
          result = '未知工具调用';
      }

      console.log('[DEBUG] 工具调用结果:', result);
      return {
        role: 'tool',
        tool_call_id: toolCall.id,
        name: functionName,
        content: result
      };
    })
  );

  // 发送所有工具调用结果
  const stream = await openai.chat.completions.create({
    messages: [
      ...messages,
      {
        role: 'assistant',
        content: assistantMessage.content || '',
        tool_calls: assistantMessage.tool_calls
      },
      ...toolResponses
    ],
    model: 'deepseek-chat',
    stream: true  // 启用流式输出
  });

  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content || '';
    if (content) {
      yield content;
    }
  }

  const endTime = performance.now()  // 记录结束时间
  console.log(`[PERF] 工具调用总耗时: ${(endTime - startTime).toFixed(2)}ms`)
};

/**
 * 处理AI助手的消息（流式版本）
 * @param {string} message - 用户最新消息
 * @param {Array} history - 消息历史记录
 * @returns {AsyncGenerator<string>} - 返回处理后的最终响应内容流
 */
export const sendMessageToAIStream = async function* (message, history = []) {
  try {
    console.log('[DEBUG] 开始处理消息:', message);

    // 首先检查是否需要使用工具
    const toolCheck = await checkToolUsage(message);
    if (!toolCheck.need_tool) {
      console.log('[DEBUG] 不需要工具调用，使用常规对话');
      // 转换历史消息格式
      const messages = history.map(msg => ({
        role: msg.isAI ? 'assistant' : 'user',
        content: msg.content
      }));
      
      // 添加系统消息和用户最新消息
      messages.unshift({
        role: 'system',
        content: '你是一个智能仪表盘的助手。'
      });
      messages.push({ role: 'user', content: message });

      // 使用流式对话处理
      yield* handleRegularConversationStream(messages);
      return;
    }

    console.log('[DEBUG] 需要工具调用，准备使用工具:', toolCheck.tool_name);

    // 转换历史消息格式（包含工具调用信息）
    const messages = history.map(msg => ({
      role: msg.isAI ? 'assistant' : 'user',
      content: msg.content,
      tool_calls: msg.tool_calls,
      tool_call_id: msg.tool_call_id
    }));

    // 添加系统消息和用户最新消息
    messages.unshift({
      role: 'system',
      content: '你是一个智能仪表盘的助手。仅在用户明确要求天气信息并提供有效地点时调用"get_weather"功能。'
    });
    messages.push({ role: 'user', content: message });

    // 第一步：发送消息给AI
    const completion = await openai.chat.completions.create({
      messages,
      model: 'deepseek-chat',
      temperature: 1.0,
      tools: functions_tools, // 使用导入的工具定义，来自 functionDescription.js
      tool_choice: 'auto'
    });

    console.log('[DEBUG] API响应:', completion);
    const assistantMessage = completion.choices[0].message;

    if (assistantMessage.tool_calls) {
      yield* handleToolCall(assistantMessage, messages);
      return;
    }

    yield assistantMessage.content || '';
  } catch (error) {
    console.error('[ERROR] 发生错误:', error);
    yield '抱歉，AI 助手暂时无法响应，请稍后再试。';
  }
};
