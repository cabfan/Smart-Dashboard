from typing import Dict, List, Optional
import numpy as np
import re

class BaseIntentRecognizer:
    def __init__(self):
        self.command_prefix = '@'
        self.commands = set()  # 子类将定义支持的命令
        
    def _quick_match(self, text: str) -> bool:
        """检查是否是命令模式"""
        if not text.startswith(self.command_prefix):
            return False
        command = text[1:].strip().split()[0]  # 获取@后的第一个词
        return command in self.commands
        
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
        self.commands = {'天气', '查天气', '查询天气'}
        self.city_pattern = r'([一-龥]+?(?:省|市|区|县|镇))'

    def _extract_city(self, text: str) -> str:
        """从文本中提取城市名"""
        city_match = re.search(self.city_pattern, text)
        if city_match:
            return city_match.group(1)
        # 如果找不到城市名，从文本中查找已知城市名
        known_cities = {'北京', '上海', '广州', '深圳', '杭州', '西安'}
        for city in known_cities:
            if city in text:
                return city
        return ''

    def analyze_intent(self, text: str) -> Dict:
        # 首先检查是否是命令格式
        if not text.startswith(self.command_prefix):
            return {
                'is_match': False,
                'confidence': 0.0,
                'intent_type': None,
                'matching_method': None
            }

        # 分割命令和参数
        parts = text[1:].strip().split(maxsplit=1)
        if len(parts) < 2:  # 如果没有参数部分
            return {
                'is_match': False,
                'confidence': 0.0,
                'intent_type': None,
                'matching_method': None
            }

        command, params = parts
        if command in self.commands:
            # 提取城市名
            city = self._extract_city(params)
            if not city:  # 如果没有找到城市名
                return {
                    'is_match': False,
                    'confidence': 0.0,
                    'intent_type': None,
                    'matching_method': None
                }

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
        self.commands = {'时间', '查时间', '当前时间', '现在时间'}

    def analyze_intent(self, text: str) -> Dict:
        # 检查是否是完整的时间查询命令
        if text.startswith(self.command_prefix):
            command = text[1:].strip()
            if command in self.commands:
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

class DatabaseQueryRecognizer(BaseIntentRecognizer):
    def __init__(self):
        super().__init__()
        self.commands = {
            '查询', '统计', '查找', '搜索',
            '查询任务', '统计任务', '查找任务', '搜索任务',
            '任务列表', '任务统计'
        }

    def analyze_intent(self, text: str) -> Dict:
        # 检查是否是完整的数据库查询命令
        if not text.startswith(self.command_prefix):
            return {
                'is_match': False,
                'confidence': 0.0,
                'intent_type': None,
                'matching_method': None
            }

        parts = text[1:].strip().split(maxsplit=1)
        command = parts[0]
        params = parts[1] if len(parts) > 1 else ''

        if command in self.commands:
            return {
                'is_match': True,
                'confidence': 0.9,
                'intent_type': 'database_query',
                'matching_method': 'quick_match',
                'params': {'question': params or command}  # 如果没有参数，使用命令本身
            }
        return {
            'is_match': False,
            'confidence': 0.0,
            'intent_type': None,
            'matching_method': None
        } 