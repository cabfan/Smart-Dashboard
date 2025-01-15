from typing import Dict, List, Optional
import numpy as np
import re

class BaseIntentRecognizer:
    def __init__(self):
        self.quick_patterns = []
        self.keywords = {}
        self.train_examples = []
        
    def _quick_match(self, text: str) -> bool:
        """快速模式匹配"""
        return False
        
    def _vector_similarity(self, text: str) -> float:
        """向量相似度匹配"""
        return 0.0
        
    def analyze_intent(self, text: str) -> Dict:
        """分析意图"""
        return {
            'is_match': False,
            'confidence': 0.0,
            'details': None,
            'matching_method': None
        }

class WeatherIntentRecognizer(BaseIntentRecognizer):
    def __init__(self):
        super().__init__()
        self.city_pattern = r'([一-龥]+?(?:省|市|区|县|镇))'  # 匹配中文城市名
        self.keywords = {
            'weather_words': {'天气', '气温', '温度', '下雨', '下雪', '晴天', '阴天', '湿度', '查询'},
            'time_words': {'今天', '明天', '后天', '早上', '中午', '下午', '晚上'},
            'question_words': {'怎么样', '如何', '会不会', '是不是', '查询', '告诉我'}
        }
        self.quick_patterns = [
            r'.*天气.*怎么样',
            r'.*会不会下雨.*',
            r'.*温度.*多少',
            r'.*查询.*天气.*',
            r'.*天气.*查询.*',
            r'.*天气.*如何.*'
        ]

    def _quick_match(self, text: str) -> bool:
        # 检查是否包含城市名
        city = self._extract_city(text)
        if not city:
            return False
            
        # 检查是否是天气查询
        has_weather = any(word in text for word in self.keywords['weather_words'])
        if has_weather:
            return True
            
        return any(re.match(pattern, text) for pattern in self.quick_patterns)

    def _extract_city(self, text: str) -> str:
        # 尝试从文本中提取城市名
        city_match = re.search(self.city_pattern, text)
        if city_match:
            return city_match.group(1)
        # 如果找不到城市名，从文本中查找已知城市名
        known_cities = {'北京', '上海', '广州', '深圳', '杭州', '西安'}  # 可以扩充这个列表
        for city in known_cities:
            if city in text:
                return city
        return '北京'  # 默认城市

    def analyze_intent(self, text: str) -> Dict:
        if self._quick_match(text):
            city = self._extract_city(text)
            return {
                'is_match': True,
                'confidence': 0.9,
                'intent_type': 'weather',
                'matching_method': 'quick_match',
                'params': {'city': city}
            }
        return {
            'is_match': False,
            'confidence': 0.0,
            'intent_type': None,
            'matching_method': None
        }

class TimeIntentRecognizer(BaseIntentRecognizer):
    def __init__(self):
        super().__init__()
        self.keywords = {
            'time_words': {'时间', '几点', '现在', '当前'},
            'question_words': {'是', '多少', '什么'}
        }
        self.quick_patterns = [
            r'.*现在.*几点.*',
            r'.*当前时间.*',
            r'.*时间.*是.*',
        ]

    def _quick_match(self, text: str) -> bool:
        has_time = any(word in text for word in self.keywords['time_words'])
        has_question = any(word in text for word in self.keywords['question_words'])
        if has_time and has_question:
            return True
            
        return any(re.match(pattern, text) for pattern in self.quick_patterns)

    def analyze_intent(self, text: str) -> Dict:
        if self._quick_match(text):
            return {
                'is_match': True,
                'confidence': 0.9,
                'intent_type': 'time',
                'matching_method': 'quick_match'
            }
        return {
            'is_match': False,
            'confidence': 0.0,
            'intent_type': None,
            'matching_method': None
        } 