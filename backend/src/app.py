from fastapi import FastAPI, WebSocket, Form
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from src.chat.chat_manager import ChatManager
import sqlite3
import json
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv
from typing import List, Dict, Optional
import pandas as pd
import asyncio
from src.routes.websocket import WebSocketRoute
from src.routes.training import TrainingRoute
from src.routes.system import SystemRoute

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

# 初始化路由处理器
websocket_route = WebSocketRoute(chat_manager, client)
training_route = TrainingRoute(chat_manager)
system_route = SystemRoute()

# WebSocket 路由
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):  # 添加类型注解
    try:
        await websocket.accept()
        await websocket_route.handle_connection(websocket)
    except Exception as e:
        print(f"WebSocket connection error: {e}")

# 训练数据管理路由
@app.get("/api/training/list")
async def list_training_data():
    return await training_route.list_training_data()

@app.post("/api/training/add")
async def add_training_data(
    data_type: str = Form(...),
    content: str = Form(...),
    question: Optional[str] = Form(None),
    title: Optional[str] = Form(""),  # 添加标题参数
    note: Optional[str] = Form("")    # 添加备注参数
):
    return await training_route.add_training_data(
        data_type=data_type,
        content=content,
        question=question,
        title=title,
        note=note
    )

@app.delete("/api/training/{training_id}")
async def delete_training_data(training_id: str):
    return await training_route.delete_training_data(training_id)

# 系统路由
@app.get("/api/current-time")
async def get_current_time():
    return await system_route.get_current_time()

@app.get("/")
async def health_check():
    return await system_route.health_check()

# 启动时初始化
@app.on_event("startup")
async def startup_event():
    print("Starting application initialization...")
    check_env_variables()
    print("Environment variables checked")
    
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=3001, reload=True)