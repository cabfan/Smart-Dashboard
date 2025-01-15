from datetime import datetime
import pytz
import json
from typing import Dict, Any
import os
from .vanna_service import VannaService

class IntentHandler:
    def __init__(self):
        self.vanna_service = VannaService(config={
            'api_key': os.getenv('OPENAI_API_KEY'),
            'model': os.getenv('OPENAI_MODEL', 'gpt-4')
        })

    async def handle_weather_intent(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理天气意图"""
        try:
            city = params.get('params', {}).get('city', '北京')
            # 这里应该调用真实的天气 API
            return {
                "success": True,
                "data": {
                    "city": city,
                    "temperature": "25°C",
                    "weather": "晴",
                    "humidity": "65%",
                    "wind": "东北风 3级",
                    "message": f"为您查询到{city}的天气信息"
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def handle_time_intent(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理时间意图"""
        try:
            tz = pytz.timezone('Asia/Shanghai')
            current_time = datetime.now(tz)
            return {
                "success": True,
                "data": {
                    "timestamp": current_time.isoformat(),
                    "formatted": current_time.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def handle_unknown_intent(self, text: str) -> Dict[str, Any]:
        """处理未知意图"""
        return {
            "success": True,
            "data": {
                "message": "抱歉，我不太理解您的问题。您可以尝试询问天气或时间。"
            }
        }

    async def handle_database_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理数据库查询意图"""
        try:
            question = params.get('params', {}).get('question', '')
            print("Database Query Question:", question)
            result = await self.vanna_service.process_question(question)
            print("Vanna Service Result:", result)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            } 