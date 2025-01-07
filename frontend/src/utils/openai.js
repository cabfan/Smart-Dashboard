import { createChatCompletion } from './chatUtils';
import { checkIfToolIsNeeded } from './functionDescription';
import { mockWeatherAPI, mockQueryPersonnelArchive } from './toolFunctions';

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
        case 'query_personnel_archive':
          result = await mockQueryPersonnelArchive(functionArgs.sql);
          break;
        default:
          result = '未知工具调用';
      }

      return {
        role: 'tool',
        tool_call_id: toolCall.id,
        name: functionName,
        content: result
      };
    })
  );

  // 先返回工具调用结果
  yield {
    status: 'using_tool',
    content: toolResponses.map(res => res.content).join('\n')
  };

  // 发送所有工具调用结果给AI
  const stream = await createChatCompletion({
    messages: [
      ...messages,
      {
        role: 'assistant',
        content: assistantMessage.content || '',
        tool_calls: assistantMessage.tool_calls
      },
      ...toolResponses
    ],
    temperature: 0.0
  });

  // 处理AI的最终响应
  let finalContent = '';
  let isFirstResponse = true;
  
  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content || '';
    //console.log('[DEBUG] 处理AI的最终响应:', content);
    if (content) {
      finalContent += content;
      
      // 如果是第一个响应块，先返回 using_tool 状态
      if (isFirstResponse) {
        yield {
          status: 'responding',
          content: '工具调用成功，正在生成响应...'
        };
        isFirstResponse = false;
      }
      
      // 返回实时内容
      yield {
        status: 'responding',
        content: content
      };
    }
  }

  // 确保返回最终内容
  if (finalContent) {
    yield {
      status: 'done',
      content: finalContent
    };
  } else {
    // 如果没有内容，返回默认提示
    yield {
      status: 'done',
      content: '工具调用成功，但没有返回内容。'
    };
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
      content: `你是一个有用的助手，可以根据用户需求调用以下工具：
                1. get_weather：获取特定地点的当前天气。
                2. query_personnel_archive：查询人员档案信息。

                **重要规则**：
                - 仅在用户明确要求使用工具时调用工具。
                - 如果用户只是提到相关关键词但没有明确要求使用工具，请不要调用工具。
                - 如果用户输入的内容不明确，请询问用户是否需要使用工具。例如：
                  - 用户输入："杭州" → 你可以回复："您是否需要获取杭州的天气信息？"
                  - 用户输入："人员信息" → 你可以回复："您是否需要查询人员档案信息？"`
    });
    messages.push({ role: 'user', content: message });

    console.log('[DEBUG] 发送的消息:', messages);

    // 第一步：发送消息给AI（流式版本）
    const stream = await createChatCompletion({
      messages,
      temperature: 0.0
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
        //console.log('[DEBUG] 返回内容:', chunk.choices[0].delta.content);
        yield { 
          status: 'responding',
          content: chunk.choices[0].delta.content 
        };
      }
    }
    // 如果需要工具调用
    if (assistantMessage.tool_calls?.length > 0) {
      // 检查是否需要调用工具
      const shouldCallTool = checkIfToolIsNeeded(assistantMessage.tool_calls, messages);
      if (shouldCallTool) {
        yield { status: 'using_tool' };  // 通知UI正在使用工具
        yield* handleToolCall(assistantMessage, messages);
      } else {
        yield { 
          status: 'responding',
          content: '哎呀，工具好像罢工了！你可以稍后再试试，或者我们聊点别的？比如，你知道为什么程序员总是分不清万圣节和圣诞节吗？因为 Oct 31 = Dec 25！😄'
        };
        /*
        // 不需要调用工具时，重新调用AI输出内容，这里可以将工具的tool_choice设置为none
        const stream = await createChatCompletion({
          messages,
          temperature: 1.3,
          tool_choice: 'none',
          tools: []
        });
        for await (const chunk of stream) {
          yield { 
            status: 'responding',
            content: chunk.choices[0]?.delta?.content || '' 
          };
        }
        */
      }
      return;
    } else {
      // 如果不需要工具调用，直接返回最终内容
      yield { 
        status: 'done',
        content: assistantMessage.content 
      };
    }

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
