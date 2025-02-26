from fastapi import WebSocket
import json
import os
from typing import Dict, Any

class WebSocketRoute:
    def __init__(self, chat_manager, openai_client):
        self.chat_manager = chat_manager
        self.client = openai_client

    async def handle_connection(self, websocket: WebSocket):
        try:
            while True:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # 处理分析请求
                if message_data.get("type") == "analysis":
                    await self._handle_analysis(websocket, message_data)
                    continue
                
                # 处理常规消息
                await self._handle_regular_message(websocket, message_data)
                
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            try:
                await websocket.close()
            except:
                pass

    async def _handle_analysis(self, websocket: WebSocket, message_data: Dict[str, Any]):
        try:
            response = await self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=[{
                    "role": "system",
                    "content": "你是一个专业的数据分析师，擅长解读数据并提供有价值的见解。"
                }] + message_data.get("messages", []),
                temperature=0.7,
                stream=False
            )
            
            result = response.choices[0].message.content if response.choices else "无法生成分析结果"
            await websocket.send_json({
                "type": "analysis_complete",
                "content": result
            })
            
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "content": f"分析失败：{str(e)}"
            })

    async def _handle_regular_message(self, websocket: WebSocket, message_data: Dict[str, Any]):
        chat_result = await self.chat_manager.process_message(
            message_data.get("messages", [{}])[-1].get("content", "")
        )
        
        if chat_result["success"] and not chat_result.get("should_fallback"):
            await self._send_success_response(websocket, chat_result)
        else:
            await self._handle_fallback(websocket, message_data)

    async def _send_success_response(self, websocket: WebSocket, chat_result: Dict[str, Any]):
        if "sql" in chat_result["data"]:
            formatted_content = {
                "message": chat_result["data"]["message"],
                "sql": chat_result["data"]["sql"],
                "results": chat_result["data"]["results"],
                "type": chat_result["data"]["type"],
                "columns": chat_result["data"].get("columns", [])
            }
        else:
            formatted_content = chat_result["data"]
        
        await websocket.send_json({
            "type": "stream",
            "content": json.dumps(formatted_content, ensure_ascii=False)
        })

    async def _handle_fallback(self, websocket: WebSocket, message_data: Dict[str, Any]):
        stream = await self.client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            messages=message_data.get("messages", []),
            stream=True,
            temperature=message_data.get("temperature", 0.7)
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                await websocket.send_json({
                    "type": "stream",
                    "content": chunk.choices[0].delta.content
                })