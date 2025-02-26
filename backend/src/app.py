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
import pandas as pd
import asyncio

# 加载环境变量
load_dotenv()

# 检查必要的环境变量
def check_env_variables():
    required_vars = ['OPENAI_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_MODEL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

# 导入 NBA 数据
def import_nba_data():
    """导入 NBA 数据"""
    try:
        csv_path = r"E:\99_my_zen\NBA_2024_Shots.csv"
        if not os.path.exists(csv_path):
            print(f"Warning: NBA data file not found at {csv_path}")
            return
        
        # 读取 CSV 文件
        df = pd.read_csv(csv_path, on_bad_lines='skip')
        
        print(f"Read {len(df)} rows from CSV")
        
        # 检查 SHOT_MADE 列的唯一值
        print("Unique values in SHOT_MADE:", df['SHOT_MADE'].unique())
        
        # 先填充空值
        df['SHOT_MADE'] = df['SHOT_MADE'].fillna('False')
        
        # 处理可能的不同布尔值表示
        bool_map = {
            'True': 1, 'true': 1, 'TRUE': 1, '1': 1, 1: 1, True: 1,
            'False': 0, 'false': 0, 'FALSE': 0, '0': 0, 0: 0, False: 0
        }
        df['SHOT_MADE'] = df['SHOT_MADE'].map(bool_map)
        
        # 确保数据类型正确
        print("Converting to integer type...")
        df['SHOT_MADE'] = df['SHOT_MADE'].astype(int)
        print("Conversion completed")
        
        # 连接到主数据库
        conn = sqlite3.connect('database.sqlite')
        
        print("Saving to database...")
        # 将数据导入到 nba_shots 表
        df.to_sql('nba_shots', conn, if_exists='replace', index=False)
        print("Data saved to database")
        
        # 获取列名用于训练 Vanna
        table_info = f"""
        NBA 投篮数据表 (nba_shots)，该表记录了NBA比赛中球员的投篮数据，包括投篮位置、投篮类型、投篮结果以及比赛时间等信息，适用于篮球数据分析和研究。包含以下字段：
        SEASON_1 & SEASON_2: 赛季指示变量，用于区分不同赛季。
        TEAM_ID: NBA API 中特定球队的唯一标识符。
        TEAM_NAME: NBA API 中特定球队的名称。
        PLAYER_ID: NBA API 中特定球员的唯一标识符。
        PLAYER_NAME: NBA API 中特定球员的名称。
        GAME_DATE: 比赛日期（格式为月-日-年，即 M-D-Y）。
        GAME_ID: NBA API 中特定比赛的唯一标识符。
        EVENT_TYPE: 表示投篮结果的字符变量（命中投篮 // 未命中投篮）。
        SHOT_MADE: 表示投篮结果的整数变量（1 表示命中，0 表示未命中）。
        ACTION_TYPE: 投篮类型的描述（例如上篮、扣篮、跳投等）。
        SHOT_TYPE: 投篮类型（2分球或3分球）。
        BASIC_ZONE: 投篮发生的球场区域名称。包括：禁区（Restricted Area）、油漆区非禁区（In the Paint (non-RA)）、中距离（Midrange）、左侧底角三分（Left Corner 3）、右侧底角三分（Right Corner 3）、弧顶三分（Above the Break）、后场（Backcourt）。
        ZONE_NAME: 投篮发生的球场侧边区域名称。包括：左侧（left）、左侧中心（left side center）、中心（center）、右侧中心（right side center）、右侧（right）。
        ZONE_ABB: 球场侧边区域的缩写。包括：(L) 左侧，(LC) 左侧中心，(C) 中心，(RC) 右侧中心，(R) 右侧。
        ZONE_RANGE: 投篮距离的区域范围。包括：小于8英尺（Less than 8 ft.）、8-16英尺（8-16 ft.）、16-24英尺（16-24 ft.）、24英尺以上（24+ ft.）。
        LOC_X: 投篮在球场平面坐标系中的X坐标（范围为0到50）。
        LOC_Y: 投篮在球场平面坐标系中的Y坐标（范围为0到50）。
        SHOT_DISTANCE: 投篮距离篮筐中心的距离，单位为英尺。
        QUARTER: 比赛的第几节。
        MINS_LEFT: 当前节剩余的分钟数。
        SECS_LEFT: 当前分钟剩余的秒数。
        
        示例查询：
        1. SELECT player_name, COUNT(*) as shots FROM nba_shots GROUP BY player_name ORDER BY shots DESC LIMIT 5;
        2. SELECT TEAM_NAME, 
                  COUNT(*) as attempts,
                  SUM(SHOT_MADE) as made,
                  ROUND(AVG(SHOT_MADE) * 100, 2) as fg_percentage 
            FROM nba_shots 
            GROUP BY TEAM_NAME 
            ORDER BY fg_percentage DESC;
        3. SELECT action_type, COUNT(*) as count FROM nba_shots WHERE shot_made = 1 GROUP BY action_type ORDER BY count DESC LIMIT 10;
        4. SELECT PLAYER_NAME,
                  COUNT(*) as attempts,
                  SUM(SHOT_MADE) as made,
                  ROUND(AVG(SHOT_MADE) * 100, 2) as fg_percentage
            FROM nba_shots
            GROUP BY PLAYER_NAME
            HAVING attempts >= 100
            ORDER BY fg_percentage DESC
            LIMIT 10;
        """
        
        # 将表信息添加到训练文档中
        with open('nba_docs.txt', 'w', encoding='utf-8') as f:
            f.write(table_info)
        
        print(f"Successfully imported NBA data with {len(df)} records")
        conn.close()
        
    except Exception as e:
        print(f"Error importing NBA data:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        print("Traceback:")
        print(traceback.format_exc())

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
    print("Starting database initialization...")
    db_path = 'database.sqlite'
    
    # 检查数据库文件权限
    try:
        if os.path.exists(db_path):
            print(f"Database file exists at {os.path.abspath(db_path)}")
        conn = sqlite3.connect(db_path)
        print("Successfully connected to database")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return
    
    c = conn.cursor()
    # 创建 NBA 投篮数据表
    print("Creating nba_shots table...")
    c.execute('''
        CREATE TABLE IF NOT EXISTS nba_shots (
            SEASON_1 TEXT,
            SEASON_2 TEXT,
            TEAM_ID TEXT,
            TEAM_NAME TEXT,
            PLAYER_ID TEXT,
            PLAYER_NAME TEXT,
            GAME_DATE TEXT,
            GAME_ID TEXT,
            EVENT_TYPE TEXT,
            SHOT_MADE INTEGER,
            ACTION_TYPE TEXT,
            SHOT_TYPE TEXT,
            BASIC_ZONE TEXT,
            ZONE_NAME TEXT,
            ZONE_ABB TEXT,
            ZONE_RANGE TEXT,
            LOC_X REAL,
            LOC_Y REAL,
            SHOT_DISTANCE REAL,
            QUARTER INTEGER,
            MINS_LEFT INTEGER,
            SECS_LEFT INTEGER
        )
    ''')
    
    print("Creating indexes for nba_shots table...")
    # 为 NBA 投篮数据表创建索引
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_team_name 
        ON nba_shots(TEAM_NAME)
    ''')
    
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_player_name 
        ON nba_shots(PLAYER_NAME)
    ''')
    
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_basic_zone 
        ON nba_shots(BASIC_ZONE)
    ''')
    
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_shot_type 
        ON nba_shots(SHOT_TYPE)
    ''')
    
    # 复合索引：用于keywords查询
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_clutch_time 
        ON nba_shots(QUARTER, MINS_LEFT)
    ''')
    
    # 复合索引：用于按日期和球员/球队查询
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_game_date_team 
        ON nba_shots(GAME_DATE, TEAM_NAME)
    ''')
    
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_game_date_player 
        ON nba_shots(GAME_DATE, PLAYER_NAME)
    ''')
    
    print("Indexes created successfully")
    
    print("Creating tasks table...")
    # 创建任务表
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("Inserting test data...")
    # 添加测试数据
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
    print("Tasks table initialized")
    
    # 导入 NBA 数据
    print("Starting NBA data import...")
    import_nba_data()
# WebSocket 连接处理
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("\n=== WebSocket connection established ===")
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            print(f"\n=== Received WebSocket message ===")
            print(f"Message type: {type(data)}")
            print(f"Message preview: {data[:200]}...")
            
            message_data = json.loads(data)
            print(f"Parsed message type: {message_data.get('type')}")
            
            # 处理分析请求
            if message_data.get("type") == "analysis":
                print("\n=== Processing Analysis Request ===")
                try:
                    print("Creating OpenAI chat completion...")
                    response = await client.chat.completions.create(
                        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                        messages=[{
                            "role": "system",
                            "content": "你是一个专业的数据分析师，擅长解读数据并提供有价值的见解。"
                        }] + message_data.get("messages", []),
                        temperature=0.7,
                        stream=False
                    )
                    
                    print("OpenAI response received")
                    print(f"Response choices: {len(response.choices)}")
                    
                    # 返回分析结果
                    result = response.choices[0].message.content if response.choices else "无法生成分析结果"
                    print(f"Analysis result preview: {result[:200]}...")
                    
                    await websocket.send_json({
                        "type": "analysis_complete",
                        "content": result
                    })
                    print("Analysis result sent to client")
                    
                except Exception as e:
                    print(f"\n=== Analysis Error ===")
                    print(f"Error type: {type(e)}")
                    print(f"Error message: {str(e)}")
                    print(f"Error details: {e.__dict__}")
                    await websocket.send_json({
                        "type": "error",
                        "content": f"分析失败：{str(e)}"
                    })
                continue
            
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


# 添加新的路由处理向量数据库管理
@app.get("/api/training/list")
async def list_training_data():
    """获取所有训练数据列表"""
    try:
        training_data = chat_manager.vanna_service.get_training_data()
        return {
            "success": True,
            "data": training_data
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"获取训练数据失败: {str(e)}"
        }

@app.post("/api/training/add")
async def add_training_data(
    data_type: str,
    content: str,
    question: str = None
):
    """添加新的训练数据"""
    try:
        training_id = chat_manager.vanna_service.add_training_data(
            data_type=data_type,
            content=content,
            question=question
        )
        
        return {
            "success": True,
            "data": {
                "id": training_id,
                "message": "训练数据添加成功"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@app.delete("/api/training/{training_id}")
async def delete_training_data(training_id: str):
    """删除指定的训练数据"""
    try:
        chat_manager.vanna_service.remove_training_data(training_id)
        return {
            "success": True,
            "message": "训练数据删除成功"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"删除训练数据失败: {str(e)}"
        }

# 启动时初始化
@app.on_event("startup")
async def startup_event():
    print("Starting application initialization...")
    check_env_variables()
    print("Environment variables checked")
    
    # 先初始化数据库和导入数据
    # init_db()
    print("Database and data import completed")
    
    # 重新初始化 chat_manager 以加载新的训练数据
    global chat_manager
    chat_manager = ChatManager()
    print("Chat manager reinitialized with new training data")
    
    print("Database initialization completed")

    
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=3001, reload=True)