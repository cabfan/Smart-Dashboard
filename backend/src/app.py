from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from src.chat.chat_manager import ChatManager
import sqlite3
import json
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv
from typing import List, Dict

# 加载环境变量
load_dotenv()

# 检查必要的环境变量
def check_env_variables():
    required_vars = ['OPENAI_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_MODEL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

app = FastAPI()
chat_manager = ChatManager()

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 OpenAI 客户端
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    default_headers={
        "Content-Type": "application/json",
    }
)

# 数据库初始化
def init_db():
    conn = sqlite3.connect('database.sqlite')
    c = conn.cursor()
    
    # 创建表
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 添加一些测试数据
    c.execute('DELETE FROM tasks')  # 清空现有数据
    test_data = [
        ('完成项目报告', '编写第一季度项目进展报告', 'pending', '2024-03-14 10:00:00'),
        ('客户会议', '与客户讨论新需求', 'completed', '2024-03-13 14:30:00'),
        ('代码审查', '审查团队提交的新功能代码', 'pending', '2024-03-14 09:00:00'),
        ('系统测试', '执行系统集成测试', 'pending', '2024-03-14 11:30:00'),
        ('文档更新', '更新API文档', 'completed', '2024-03-12 16:00:00'),
    ]
    
    c.executemany('''
        INSERT INTO tasks (title, description, status, created_at)
        VALUES (?, ?, ?, ?)
    ''', test_data)
    
    conn.commit()
    conn.close()

# WebSocket 连接处理
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # 先进行意图识别和处理
            chat_result = await chat_manager.process_message(
                message_data.get("messages", [{}])[-1].get("content", "")
            )
            print("Chat Manager Result:", chat_result)
            
            # 如果有明确的意图匹配且处理成功
            if chat_result["success"] and not chat_result.get("should_fallback"):
                print("Original chat result:", chat_result)
                # 根据不同的意图类型格式化内容
                if "sql" in chat_result["data"]:
                    # 数据库查询结果
                    formatted_content = {
                        "message": chat_result["data"]["message"],
                        "sql": chat_result["data"]["sql"],
                        "results": chat_result["data"]["results"],
                        "type": chat_result["data"]["type"],
                        "columns": chat_result["data"].get("columns", [])
                    }
                else:
                    # 其他类型的响应（天气、时间等）
                    formatted_content = chat_result["data"]
                
                print("Formatted content:", formatted_content)
                await websocket.send_json({
                    "type": "stream",
                    "content": json.dumps(formatted_content, ensure_ascii=False)
                })
                continue
            
            # 如果没有明确意图或需要降级处理，使用 OpenAI 处理
            try:
                stream = await client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                    messages=message_data.get("messages", []),
                    stream=True,
                    temperature=message_data.get("temperature", 0.7)
                )

                # 流式响应
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        await websocket.send_json({
                            "type": "stream",
                            "content": chunk.choices[0].delta.content
                        })
                    elif chunk.choices[0].delta.tool_calls:
                        # 将工具调用对象转换为可序列化的字典
                        tool_calls_data = []
                        for tool_call in chunk.choices[0].delta.tool_calls:
                            tool_call_dict = {
                                "index": tool_call.index if hasattr(tool_call, 'index') else None,
                                "id": tool_call.id if hasattr(tool_call, 'id') else None,
                                "type": "function",
                                "function": {
                                    "name": tool_call.function.name if hasattr(tool_call.function, 'name') else "",
                                    "arguments": tool_call.function.arguments if hasattr(tool_call.function, 'arguments') else ""
                                }
                            }
                            tool_calls_data.append(tool_call_dict)
                        
                        await websocket.send_json({
                            "type": "tool_calls",
                            "tool_calls": tool_calls_data
                        })

            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "content": str(e)
                })
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass

# 获取当前北京时间
@app.get("/api/current-time")
async def get_current_time():
    try:
        # 获取北京时区
        tz = pytz.timezone('Asia/Shanghai')
        # 获取当前时间并转换为北京时间
        current_time = datetime.now(tz)
        
        return {
            "success": True,
            "timestamp": current_time.isoformat(),
            "formatted": current_time.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# 健康检查接口
@app.get("/api/health")
async def health_check():
    try:
        # 检查数据库连接
        conn = sqlite3.connect('database.sqlite')
        conn.close()
        
        # 检查 OpenAI API 配置
        if not os.getenv("OPENAI_API_KEY"):
            return {
                "status": "warning",
                "message": "OpenAI API key not configured"
            }
        
        return {
            "status": "ok",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

# 启动时初始化
@app.on_event("startup")
async def startup_event():
    check_env_variables()
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=3000, reload=True) 