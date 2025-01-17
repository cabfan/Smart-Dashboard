import aiohttp
from typing import Dict, Any
import os
import json

class WeatherService:
    def __init__(self):
        self.api_key = os.getenv("WEATHER_API_KEY")
        self.geo_api = "https://geoapi.qweather.com/v2/city/lookup"
        self.weather_api = "https://devapi.qweather.com/v7/weather/now"

    async def get_location_id(self, city: str) -> str:
        """获取城市的位置 ID"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    'location': city,
                    'range': 'cn',
                    'key': self.api_key
                }
                async with session.get(self.geo_api, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['code'] == '200' and data['location']:
                            # 返回第一个匹配城市的 ID
                            return data['location'][0]['id']
                    raise Exception(f"无法获取{city}的位置信息")
        except Exception as e:
            print(f"Error getting location ID: {e}")
            raise

    async def get_weather(self, city: str) -> Dict[str, Any]:
        """获取城市天气信息"""
        try:
            # 先获取城市 ID
            location_id = await self.get_location_id(city)
            
            # 查询天气信息
            async with aiohttp.ClientSession() as session:
                params = {
                    'location': location_id,
                    'key': self.api_key
                }
                async with session.get(self.weather_api, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['code'] == '200':
                            weather_data = data['now']
                            return {
                                "city": city,
                                "temperature": f"{weather_data['temp']}°C",
                                "weather": weather_data['text'],
                                "humidity": f"{weather_data['humidity']}%",
                                "wind": f"{weather_data['windDir']} {weather_data['windScale']}级",
                                "message": f"为您查询到{city}的天气信息"
                            }
                        else:
                            raise Exception(f"天气 API 返回错误: {data['code']}")
                    else:
                        raise Exception(f"Weather API returned status {response.status}")
                        
        except Exception as e:
            print(f"Error getting weather: {e}")
            return {
                "message": f"获取{city}的天气信息失败",
                "error": str(e)
            } 