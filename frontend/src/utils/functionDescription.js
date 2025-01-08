// 导出工具数组
export const functions_tools = [
    {
        type: "function",
        function: {
            name: "get_weather",
            description: "获取特定地点的当前天气。仅在用户明确要求天气信息并提供有效地点时调用此功能。例如：'杭州的天气怎么样？' 或 '告诉我北京的天气。' 如果用户只是提到城市名称但没有明确要求天气信息，请不要调用此功能。",
            parameters: {
                type: "object",
                properties: {
                    location: {
                        type: "string",
                        description: "城市和国家，例如：杭州，中国。"
                    }
                },
                required: ["location"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "query_personnel_archive",
            description: "根据提供的SQL语句查询人员档案信息。返回结果包括姓名、年龄、性别、政治面貌、婚姻状况等基本人事信息。仅在用户明确要求查询人员档案信息时调用此功能。",
            parameters: {
                type: "object",
                properties: {
                    sql: {
                        type: "string",
                        description: "用于查询人员档案信息的SQL语句。必须包含SELECT语句，且只能查询姓名、年龄、性别、政治面貌、婚姻状况等基本信息。"
                    }
                },
                required: ["sql"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "get_current_time",
            description: "获取当前北京时间。"
        }
    }
];

// 检查是否需要调用工具
export const checkIfToolIsNeeded = (toolCalls, messages) => {
    // 如果没有工具调用，直接返回 false
    if (!toolCalls || toolCalls.length === 0) {
      return false;
    }
  
    // 遍历所有工具调用
    for (const toolCall of toolCalls) {
      const toolName = toolCall.function.name;
      let toolArgs;

      // 尝试解析工具参数
      try {
        toolArgs = JSON.parse(toolCall.function.arguments);
      } catch (error) {
        console.log("工具参数解析失败，反馈用户不支持多工具能力。");
        return false;
      }
  
      // 根据工具名称和参数判断是否需要调用
      switch (toolName) {
        case "get_weather":
          // 检查是否提供了 location 参数
          if (!toolArgs.location) {
            console.log("天气工具被调用，但缺少位置信息。");
            return false;
          }
          break;
  
        case "query_personnel_archive":
          // 对其他工具进行类似的检查
          if (!isPersonnelArchiveNeeded(messages)) {
            console.log("查询人员档案工具被调用，但用户输入与查询人员档案无关。");
            return false;
          }
          break;

        case "get_current_time":
          break;
  
        default:
          console.log(`未知工具调用: ${toolName}`);
          return false;
      }
    }
  
    // 如果所有工具调用都合理，返回 true
    return true;
};

// 检查用户输入是否与天气相关
export function isWeatherRelatedQuery(messages) {
    return true;
    const userMessage = messages[messages.length - 1]?.content || "";
    const weatherKeywords = ["天气", "温度", "天气预报", "下雨", "晴天"];
    return weatherKeywords.some(keyword => userMessage.toLowerCase().includes(keyword));
}

// 检查用户输入是否与人员档案相关
export function isPersonnelArchiveNeeded(messages) {
    return true;
    const userMessage = messages[messages.length - 1]?.content || "";
    const keywords = ["人员档案", "档案", "人员", "查询"];
    return keywords.some(keyword => userMessage.toLowerCase().includes(keyword));
}