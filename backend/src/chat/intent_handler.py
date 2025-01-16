from datetime import datetime
import pytz
import json
from typing import Dict, Any
import os
import aiohttp
from .vanna_service import VannaService

class IntentHandler:
    def __init__(self):
        self.weather_api_key = "46c9ded06bd84ce5b833058495a1fd17"  # 和前端使用相同的 key
        self.vanna_service = VannaService(config={
            'api_key': os.getenv('OPENAI_API_KEY'),
            'model': os.getenv('OPENAI_MODEL', 'deepseek-chat'),
            'base_url': os.getenv('OPENAI_BASE_URL'),
            'temperature': 0.7,
            'max_tokens': 2000,
            'verbose': True
        })

    async def handle_weather_intent(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理天气意图"""
        try:
            city = params.get('params', {}).get('city', '')
            if not city:
                return {
                    "success": False,
                    "error": "未指定城市名"
                }
            
            async with aiohttp.ClientSession() as session:
                # 1. 先查询城市 ID
                lookup_url = f"https://geoapi.qweather.com/v2/city/lookup"
                params = {
                    "location": city,
                    "range": "cn",
                    "key": self.weather_api_key
                }
                
                async with session.get(lookup_url, params=params) as response:
                    lookup_data = await response.json()
                    
                    if lookup_data.get("code") != "200" or not lookup_data.get("location"):
                        return {
                            "success": False,
                            "error": f"无法找到 {city} 的位置信息"
                        }
                    
                    # 获取城市 ID 和标准城市名
                    city_id = lookup_data["location"][0]["id"]
                    city_name = lookup_data["location"][0]["name"]
                    
                    # 2. 查询实时天气
                    weather_url = f"https://devapi.qweather.com/v7/weather/now"
                    params = {
                        "location": city_id,
                        "key": self.weather_api_key
                    }
                    
                    async with session.get(weather_url, params=params) as response:
                        weather_data = await response.json()
                        
                        if weather_data.get("code") != "200":
                            return {
                                "success": False,
                                "error": f"获取 {city_name} 天气信息失败"
                            }
                        
                        weather = weather_data["now"]
                        return {
                            "success": True,
                            "data": {
                                "city": city_name,
                                "temperature": f"{weather['temp']}°C",
                                "weather": weather['text'],
                                "humidity": f"{weather['humidity']}%",
                                "wind": f"{weather['windDir']} {weather['windScale']}级",
                                "message": f"为您查询到{city_name}的天气信息"
                            }
                        }

        except Exception as e:
            return {
                "success": False,
                "error": f"获取天气信息失败: {str(e)}"
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