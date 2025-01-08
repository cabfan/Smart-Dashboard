import { createChatCompletion } from './chatUtils';
import { checkIfToolIsNeeded, functions_tools } from './functionDescription';
import { mockWeatherAPI, mockQueryPersonnelArchive, getCurrentTime } from './toolFunctions';

/**
 * 转换历史消息格式
 * @param {Array} history - 原始历史消息记录
 * @returns {Array} - 转换后的消息数组
 */
const transformHistoryMessages = (history) => {
  return history
    // 先过滤掉不需要的消息
    .filter(msg => msg.status !== 'thinking' && msg.content !== '')
    // 然后进行转换
    .map(msg => {
      // 创建基本的消息对象
      const message = {
        role: msg.isAI ? 'assistant' : 'user',  // 判断消息的角色
        content: msg.content                    // 设置消息内容
      };
    
      // 如果 tool_calls 存在，添加它到消息对象中
      if (msg.tool_calls) {
        message.tool_calls = msg.tool_calls;
      }
    
      // 如果 tool_call_id 存在，添加它到消息对象中
      if (msg.tool_call_id) {
        message.tool_call_id = msg.tool_call_id;
      }
    
      return message;
    });
};

/**
 * 处理工具调用
 * @param {Object} assistantMessage - AI助手的消息对象
 * @param {Array} messages - 完整的消息历史记录
 * @returns {AsyncGenerator<string>} - 返回处理后的最终响应内容流
 */
const handleToolCall = async function* (assistantMessage, messages) {
 
  console.log('[DEBUG] 检测到工具调用:', assistantMessage.tool_calls);

  // 收集所有工具调用结果
  const toolResponses = await Promise.all(
    assistantMessage.tool_calls.map(async (toolCall) => {
      const functionName = toolCall.function.name; // 获取工具函数名称
      const functionArgs = JSON.parse(toolCall.function.arguments); // 解析工具函数参数

      console.log('[DEBUG] 工具调用详情:', { functionName, functionArgs });

      let result;
      switch (functionName) {
        case 'get_weather':
          result = await mockWeatherAPI(functionArgs.location); // 调用天气API
          break;
        case 'query_personnel_archive':
          result = await mockQueryPersonnelArchive(functionArgs.sql); // 调用人员档案查询API
          break;
        case 'get_current_time':
          result = await getCurrentTime(); // 调用获取当前时间API
          break;
        default:
          result = '未知工具调用'; // 处理未知工具调用
      }

      // 确保返回有效结果
      if (!result) {
        result = '工具调用成功，但未返回有效信息';
      }

      console.log('[DEBUG] 工具调用结果:', result);

      return {
        role: 'tool',
        tool_call_id: toolCall.id,
        name: functionName,
        content: result // 直接返回工具的结果，因为工具是自己辨析的，可以100%保证输出JSON的格式。
      };
    })
  );

  // 返回工具调用结果
  for(const toolResponse of toolResponses) {
    switch(toolResponse.name) {
      case 'get_weather':
        yield {
          status: 'tool_result',
          componentType: 'WeatherCard',
          content: JSON.stringify(toolResponse.content)
        }
        break;
      case 'query_personnel_archive':
        yield {
          status: 'responding',
          content: JSON.stringify(toolResponse.content)
        }
        break;
      case 'get_current_time': 
        yield {
          status: 'responding',
          content: JSON.stringify(toolResponse.content)
        }
        break;
      default:
        yield {
          status: 'responding',
          content: '调用工具失败咯，甚至都不知道什么工具~'
        }
        break;
    }
  }
  yield {
    status: 'done',
    content: '工具调用完成咯~'
  }
/** 暂时处理为，调用工具不再回传给AI进行处理，我自己处理显示效果，这样能避免隐私泄漏和更灵活的绘制方法
   * 
   * 
  // 先返回工具调用结果
  yield {
    status: 'using_tool',
    content: toolResponses
      .map(res => {
        try {
          const parsed = JSON.parse(res.content);
          return typeof parsed === 'string' ? parsed : JSON.stringify(parsed);
        } catch {
          return res.content;
        }
      })
      .join('\n')
  };
  
  // 将助手消息和工具调用结果添加到消息历史中
  messages.push({
    role: 'assistant',
    content: assistantMessage.content || '',
    tool_calls: assistantMessage.tool_calls
  });
  messages.push(...toolResponses);

  // 发送所有工具调用结果给AI
  const stream = await createChatCompletion({
    messages: messages,
    temperature: 0.0,
    tools: functions_tools,
    tool_choice: 'auto',
  });

  // 处理AI的最终响应
  let finalContent = ''; // 存储最终生成的内容
  let hasContent = false; // 标记是否有内容生成

  for await (const chunk of stream) {
    // 检查是否有内容
    if (chunk.choices[0]?.delta?.content) {
      finalContent += chunk.choices[0].delta.content; // 累加生成的内容
      hasContent = false; // 标记为有内容
      yield {
        status: 'responding',
        content: chunk.choices[0].delta.content // 返回当前生成的内容
      };
    }
  }

  // 如果没有内容，直接返回工具调用结果
  if (!hasContent) {
    console.log('[DEBUG] 没有生成内容，返回工具调用结果');
    const toolResults = toolResponses.map(res => {
      try {
        const parsed = JSON.parse(res.content);
        return typeof parsed === 'string' ? parsed : JSON.stringify(parsed);
      } catch {
        return res.content;
      }
    }).join('\n');
    
    yield {
      status: 'done',
      content: toolResults || '工具调用成功，但没有返回内容。'
    };
  } else {
    yield {
      status: 'done',
      content: finalContent // 返回最终生成的内容
    };
  }
   */
};

/**
 * 处理AI助手的消息（流式版本）
 * @param {string} message - 用户最新消息
 * @param {Array} history - 消息历史记录
 * @returns {AsyncGenerator<string>} - 返回处理后的最终响应内容流
 */
export const sendMessageToAIStream = async function* (history = []) {
  try {
    const startTime = performance.now();
    
    // 转换历史消息格式
    const messages = transformHistoryMessages(history);

    // 添加系统消息和用户最新消息
    messages.unshift({
      role: 'system',
      content: `你是一个高效的助手，能够根据用户需求调用以下工具：

get_weather：获取特定地点的当前天气。
query_personnel_archive：查询人员档案信息。
get_current_time：获取当前北京时间。
重要规则：

识别用户意图： 首先要识别用户意图。如果用户的需求包含多个不同的任务（例如天气查询和人员档案查询），tool_calls 应返回多个独立的工具调用。

工具调用时机：

仅在用户明确要求时调用工具。例如，用户输入：“请查询杭州的天气”，你可以调用 get_weather。
如果用户仅提到相关关键词，但没有明确请求工具调用（如提到“天气”或“人员信息”），请先询问用户是否需要工具帮助。例如：
用户输入：“杭州” → 你可以回复：“您是否需要获取杭州的天气信息？”
用户输入：“人员信息” → 你可以回复：“您是否需要查询人员档案信息？”
处理多个意图：

如果用户同时提到多个任务（例如，查询天气和人员档案），请根据需求生成多个工具调用。例如：
用户输入：“查询杭州的天气和张三的档案” → 生成两个工具调用，分别为 get_weather 和 query_personnel_archive。
请确保每个工具调用都具备正确的 arguments 和 name。
清晰的分隔和处理：

如果用户的输入含有多个意图，请在生成 tool_calls 时分开每个工具调用，确保每个调用都有自己的明确任务和参数。
如果用户的输入不明确，请主动询问用户的具体需求。`
    });

    console.log('[DEBUG] 1、发送的消息:', { 
      messages,
      temperature: 0.0,
      tools: functions_tools,
      tool_choice: 'auto'
    });

    // 第一步：发送消息给AI（流式版本）
    const stream = await createChatCompletion({ 
      messages,
      temperature: 1.0,
      tools: functions_tools,
      tool_choice: 'auto'
    });

    let assistantMessage = { content: '', tool_calls: [] }; // 存储助手生成的消息和工具调用信息
    let isFirstChunk = true; // 标记是否为首个响应块
    let firstChunkTime = null; // 存储首个响应块的时间

    for await (const chunk of stream) {
      if (!firstChunkTime) {
        firstChunkTime = performance.now();
        console.log(`[PERF] 首字节响应时间: ${(firstChunkTime - startTime).toFixed(2)}ms`);
      }

      if (isFirstChunk) {
        yield { status: 'thinking' };  // 通知UI正在思考
        isFirstChunk = false;
      }
      
      // 收集消息内容
      if (chunk.choices[0]?.delta?.content) {
        assistantMessage.content += chunk.choices[0].delta.content; // 累加助手生成的内容
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
          content: chunk.choices[0].delta.content // 返回当前生成的内容
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
        // 以下是不需要调用工具时，重新调用AI输出内容

        //获取messages最后一条
        const lastMessage = messages[messages.length - 1];

        // 创建系统提示词消息
        const newSystemPrompt = {
          role: "system", // 系统消息
          content: "你是一个智能助手，告诉用户，在一次问答中，进行多次查询意图，目前还不至此。"
        };
        // 创建新的聊天消息，包含系统提示词和最后一条消息
        const newChatMessages = [
          newSystemPrompt, // 添加系统提示词
          lastMessage
        ];

        // 不需要调用工具时，重新调用AI输出内容，这里可以将工具的tool_choice设置为none
        const stream = await createChatCompletion({
          messages: newChatMessages,
          temperature: 1.3,
          tool_choice: 'none'
        });
        for await (const chunk of stream) {
          console.log(chunk)
          yield { 
            status: 'responding',
            content: chunk.choices[0]?.delta?.content || '' // 返回当前生成的内容
          };
        }
      }
      return;
    } else {
      // 如果不需要工具调用，直接返回最终内容
      yield { 
        status: 'done',
        content: assistantMessage.content // 返回助手生成的最终内容
      };
    }

    const endTime = performance.now();
    console.log(`[PERF] 处理消息总耗时: ${(endTime - startTime).toFixed(2)}ms`);
  } catch (error) {
    console.error('[ERROR] 发生错误:', error);
    yield { 
      status: 'error',
      content: '抱歉，AI 助手暂时无法响应，请稍后再试。'
    };
  }
};
