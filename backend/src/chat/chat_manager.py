from typing import Dict, List, Any
from .intent_recognizer import WeatherIntentRecognizer, TimeIntentRecognizer, DatabaseQueryRecognizer
from .intent_handler import IntentHandler

class ChatManager:
    def __init__(self):
        self.recognizers = [
            WeatherIntentRecognizer(),
            TimeIntentRecognizer(),
            DatabaseQueryRecognizer()
        ]
        self.handler = IntentHandler()

    async def process_message(self, text: str) -> Dict[str, Any]:
        """处理用户消息"""
        # 1. 意图识别
        print("Processing message:", text)
        intent_results = []
        for recognizer in self.recognizers:
            result = recognizer.analyze_intent(text)
            if result['is_match']:
                intent_results.append(result)
                print("Matched Intent:", result)

        # 2. 选择最佳意图
        if intent_results:
            best_intent = max(intent_results, key=lambda x: x['confidence'])
            print("Best Intent:", best_intent)
            
            # 3. 处理意图
            if best_intent['intent_type'] == 'weather':
                return await self.handler.handle_weather_intent(best_intent)
            elif best_intent['intent_type'] == 'time':
                return await self.handler.handle_time_intent({'text': text})
            elif best_intent['intent_type'] == 'database_query':
                result = await self.handler.handle_database_query(best_intent)
                print("Database Query Result:", result)
                return result
        
        # 4. 如果没有匹配到特定意图，返回 None，让外层处理
        return {
            "success": False,
            "should_fallback": True
        } 