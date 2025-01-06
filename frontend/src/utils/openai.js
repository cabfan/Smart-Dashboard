import OpenAI from 'openai';
// 从functionDescription导入工具定义
import { functions_tools } from './functionDescription';

const openai = new OpenAI({
  baseURL: 'https://api.deepseek.com',
  apiKey: 'sk-e09b1c2850754858b41d8579766b60e2',
  dangerouslyAllowBrowser: true
});


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
  const startTime = performance.now()
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

      console.log('[DEBUG] 工具调用结果:', {
        role: 'tool',
        tool_call_id: toolCall.id,
        name: functionName,
        content: result
      });

      return {
        role: 'tool',
        tool_call_id: toolCall.id,
        name: functionName,
        content: result
      };
    })
  );
  console.log('[DEBUG] 所有工具调用结果:', toolResponses);
  console.log('Debug: 开始发送所有工具调用结果，调用openai.chat.completions.create');
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
    stream: true
  });

  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content || '';
    if (content) {
      yield { 
        status: 'responding',
        content: content 
      };
    }
  }

  const endTime = performance.now()
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
    const startTime = performance.now()

    // 转换历史消息格式
    const messages = history.map(msg => ({
      role: msg.isAI ? 'assistant' : 'user',
      content: msg.content,
      tool_calls: msg.tool_calls,
      tool_call_id: msg.tool_call_id
    }));

    // 添加系统消息和用户最新消息
    messages.unshift({
      role: 'system',
      content: `你是一个智能仪表盘的助手，在正确理解用户的意图之后，
      再进行判断是否需要调用工具。所有工具我都会传递给你，
      你只需要根据用户意图进行判断是否需要调用工具，如果需要调用工具，
      则调用工具，如果不需要调用工具，则直接返回结果。`
    });
    messages.push({ role: 'user', content: message });

    // 第一步：发送消息给AI（流式版本）
    const stream = await openai.chat.completions.create({
      messages,
      model: 'deepseek-chat',
      temperature: 1.0,
      tools: functions_tools,
      tool_choice: 'auto',
      stream: true
    });

    let assistantMessage = { content: '', tool_calls: [] };
    let isFirstChunk = true;
    let firstChunkTime = null;

    for await (const chunk of stream) {
      if (!firstChunkTime) {
        firstChunkTime = performance.now()
        console.log(`[PERF] 首字节响应时间: ${(firstChunkTime - startTime).toFixed(2)}ms`)
      }

      if (isFirstChunk) {
        yield { status: 'thinking' };  // 通知UI正在思考
        isFirstChunk = false;
      }

      // 收集消息内容
      if (chunk.choices[0]?.delta?.content) {
        assistantMessage.content += chunk.choices[0].delta.content;
      }

      // 收集工具调用信息
      if (chunk.choices[0]?.delta?.tool_calls) {
        // 确保tool_calls数组存在
        if (!assistantMessage.tool_calls) {
          assistantMessage.tool_calls = [];
        }
        
        // 处理每个工具调用
        chunk.choices[0].delta.tool_calls.forEach((toolCall, index) => {
          if (!assistantMessage.tool_calls[index]) {
            assistantMessage.tool_calls[index] = {
              id: toolCall.id || '',
              type: 'function',
              function: {
                name: '',
                arguments: ''
              }
            };
          }
          
          // 更新工具调用信息
          if (toolCall.function?.name) {
            assistantMessage.tool_calls[index].function.name += toolCall.function.name;
          }
          if (toolCall.function?.arguments) {
            assistantMessage.tool_calls[index].function.arguments += toolCall.function.arguments;
          }
        });
      }

      // 如果已经有内容，则逐步返回
      if (chunk.choices[0]?.delta?.content) {
        yield { 
          status: 'responding',
          content: chunk.choices[0].delta.content 
        };
      }
    }

    // 如果需要工具调用
    if (assistantMessage.tool_calls?.length > 0) {
      console.log('[DEBUG] 完整工具调用信息:', assistantMessage.tool_calls);
      yield { status: 'using_tool' };  // 通知UI正在使用工具
      yield* handleToolCall(assistantMessage, messages);
      return;
    }

    // 如果不需要工具调用，直接返回最终内容
    yield { 
      status: 'done',
      content: assistantMessage.content 
    };

    const endTime = performance.now()
    console.log(`[PERF] 处理消息总耗时: ${(endTime - startTime).toFixed(2)}ms`)
  } catch (error) {
    console.error('[ERROR] 发生错误:', error);
    yield { 
      status: 'error',
      content: '抱歉，AI 助手暂时无法响应，请稍后再试。'
    };
  }
};
