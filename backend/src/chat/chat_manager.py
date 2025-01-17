from typing import Dict, List, Any
import os
from datetime import datetime
from .vanna_service import VannaService
from .weather_service import WeatherService

class ChatManager:
    def __init__(self):
        # 初始化服务
        self.vanna_service = VannaService({
            'api_key': os.getenv('OPENAI_API_KEY'),
            'model': os.getenv('OPENAI_MODEL'),
            'base_url': os.getenv('OPENAI_BASE_URL')
        })
        self.weather_service = WeatherService()

    def _extract_intent(self, message: str) -> Dict[str, Any]:
        """提取用户意图"""
        if not message.startswith('@'):
            return {"intent": "chat"}
        
        # 移除 @ 并分割命令和参数
        parts = message[1:].strip().split(maxsplit=1)
        command = parts[0].lower()
        params = parts[1] if len(parts) > 1 else ""
        
        if command == '查询统计':
            return {
                "intent": "db_query",
                "params": params
            }
        elif command == '查天气':
            return {
                "intent": "weather",
                "city": params
            }
        elif command == '当前时间':
            return {
                "intent": "time"
            }
        
        return {"intent": "unknown"}

    async def process_message(self, message: str) -> Dict[str, Any]:
        """处理用户消息"""
        intent_info = self._extract_intent(message)
        intent = intent_info.get("intent")
        
        try:
            if intent == "db_query":
                # 使用 Vanna 处理数据库查询
                query_result = await self.vanna_service.process_question(
                    message[len('@查询统计'):].strip()  # 获取完整的查询描述
                )
                return {
                    "success": True,
                    "data": query_result["data"] if query_result["success"] else {
                        "message": query_result["message"]
                    }
                }
            elif intent == "weather":
                # 处理天气查询
                weather_info = await self.weather_service.get_weather(
                    intent_info.get("city", "")
                )
                return {
                    "success": True,
                    "data": weather_info
                }
            elif intent == "time":
                # 处理时间查询
                current_time = datetime.now()
                return {
                    "success": True,
                    "data": {
                        "timestamp": current_time.isoformat(),
                        "formatted": current_time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
            else:
                return {
                    "success": False,
                    "should_fallback": True,
                    "message": "未知的命令"
                }
        except Exception as e:
            print(f"Error processing message: {e}")
            return {
                "success": False,
                "message": str(e)
            } 