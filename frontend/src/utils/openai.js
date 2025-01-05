import OpenAI from 'openai';

const openai = new OpenAI({
  baseURL: 'https://api.deepseek.com',
  apiKey: '',
  dangerouslyAllowBrowser: true
});

// 定义工具
const tools = [
  {
    type: "function",
    function: {
      name: "get_weather",
      description: "Get weather of a location",
      parameters: {
        type: "object",
        properties: {
          location: {
            type: "string",
            description: "The city and state, e.g. Hangzhou, China"
          }
        },
        required: ["location"]
      }
    }
  }
];

// 模拟天气API
const mockWeatherAPI = async (location) => {
  console.log('[DEBUG] 调用模拟天气API，位置:', location);
  return `${location} 当前天气：24℃，晴`;
};

export const sendMessageToAI = async (message, history = [], onStream) => {
  try {
    console.log('[DEBUG] 开始处理消息:', message);

    // 转换历史消息格式
    const messages = history.map(msg => ({
      role: msg.isAI ? 'assistant' : 'user',
      content: msg.content,
      tool_calls: msg.tool_calls,
      tool_call_id: msg.tool_call_id
    }));

    console.log('[DEBUG] 历史消息:', messages);

    // 添加系统消息
    messages.unshift({
      role: 'system',
      content: 'You are a helpful assistant.'
    });

    // 添加当前消息
    messages.push({
      role: 'user',
      content: message
    });

    console.log('[DEBUG] 发送给API的完整消息:', messages);

    // 第一步：发送消息给AI
    const completion = await openai.chat.completions.create({
      messages,
      model: 'deepseek-chat',
      temperature: 0.0, // 降低温度以减少多样性
      tools,
      tool_choice: 'auto'
    });

    console.log('[DEBUG] API响应:', completion);

    const assistantMessage = completion.choices[0].message;
    let fullResponse = assistantMessage.content || '';

    console.log('[DEBUG] 助手消息:', assistantMessage);

    // 如果有工具调用
    if (assistantMessage.tool_calls) {
      console.log('[DEBUG] 检测到工具调用:', assistantMessage.tool_calls);

      // 收集所有工具调用结果
      const toolResponses = await Promise.all(
        assistantMessage.tool_calls.map(async (toolCall) => {
          const functionName = toolCall.function.name;
          const functionArgs = JSON.parse(toolCall.function.arguments);

          console.log('[DEBUG] 工具调用详情:', {
            functionName,
            functionArgs
          });

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

      // 第二步：发送所有工具调用结果
      const toolResponse = await openai.chat.completions.create({
        messages: [
          ...messages,
          {
            role: 'assistant',
            content: fullResponse,
            tool_calls: assistantMessage.tool_calls
          },
          ...toolResponses
        ],
        model: 'deepseek-chat'
      });

      console.log('[DEBUG] 工具调用后的API响应:', toolResponse);
      fullResponse = toolResponse.choices[0].message.content;
    }

    console.log('[DEBUG] 最终响应:', fullResponse);
    return fullResponse;
  } catch (error) {
    console.error('[ERROR] 发生错误:', error);
    return '抱歉，AI 助手暂时无法响应，请稍后再试。';
  }
};
