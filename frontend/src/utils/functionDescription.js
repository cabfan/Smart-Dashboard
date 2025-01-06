
// 导出工具数组
export const functions_tools = [
    {
        type: "function",
        function: {
            name: "get_weather",
            description: "获取特定地点的当前天气。仅在用户明确要求天气信息并提供有效地点时调用此功能。",
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
    }
];