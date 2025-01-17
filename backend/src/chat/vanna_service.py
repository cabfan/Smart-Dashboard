from vanna.openai.openai_chat import OpenAI_Chat
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
import sqlite3
import os
from typing import Dict, Any
from ..cache.query_cache import QueryCache
from ..cache.command_cache import CommandCache  # 新增命令缓存

class VannaService(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        print("Initializing VannaService with config:", config)
        if not config or 'api_key' not in config:
            raise ValueError("API key is required for VannaService")
        
        # 确保配置完整
        required_config = ['api_key', 'model', 'base_url']
        missing_config = [key for key in required_config if key not in config]
        print("Checking required config. Missing:", missing_config if missing_config else "None")
        if missing_config:
            raise ValueError(f"Missing required configuration: {', '.join(missing_config)}")
        
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)
        self.db_path = 'database.sqlite'
        self.query_cache = QueryCache()  # 查询结果缓存
        self.command_cache = CommandCache()  # 命令到SQL的缓存
        
        self._init_vanna()
    
    def _init_vanna(self):
        """初始化 Vanna，包括训练数据"""
        # 获取数据库表结构
        ddl = self._get_database_schema()
        self.train(ddl=ddl)
        
        # 添加一些示例查询
        self.train(sql="""
            SELECT * FROM tasks 
            WHERE status = 'pending' 
            ORDER BY created_at DESC
        """)
        
        # 加载并训练 NBA 数据文档
        try:
            if os.path.exists('nba_docs.txt'):
                print("Loading NBA documentation...")
                with open('nba_docs.txt', 'r', encoding='utf-8') as f:
                    nba_docs = f.read()
                self.train(documentation=nba_docs)
                print("NBA documentation trained successfully")
            else:
                print("Warning: nba_docs.txt not found")
        except Exception as e:
            print(f"Error training NBA documentation: {e}")
        
        # 添加业务文档
        self.train(documentation="""
            tasks 表存储了所有任务记录：
            - id: 任务ID
            - title: 任务标题
            - description: 任务描述
            - status: 任务状态 (pending/completed)
            - created_at: 创建时间
        """)
        
        # 添加一些示例查询
        self.train(sql="""
            -- 查询各队投篮命中率
            SELECT 
                TEAM_NAME as team_name,
                COUNT(*) as attempts,
                SUM(SHOT_MADE) as made,
                ROUND(AVG(SHOT_MADE) * 100, 2) as fg_percentage
            FROM nba_shots
            GROUP BY TEAM_NAME
            ORDER BY fg_percentage DESC;
            
            -- 查询不同投篮区域的命中率
            SELECT 
                BASIC_ZONE as zone,
                COUNT(*) as attempts,
                SUM(SHOT_MADE) as made,
                ROUND(AVG(SHOT_MADE) * 100, 2) as fg_percentage
            FROM nba_shots
            GROUP BY BASIC_ZONE
            ORDER BY attempts DESC;
            
            -- 查询球员投篮排名（最少100次出手）
            SELECT 
                PLAYER_NAME as player,
                COUNT(*) as attempts,
                SUM(SHOT_MADE) as made,
                ROUND(AVG(SHOT_MADE) * 100, 2) as fg_percentage
            FROM nba_shots
            GROUP BY PLAYER_NAME
            HAVING attempts >= 100
            ORDER BY fg_percentage DESC
            LIMIT 10;
            
            -- 查询三分球命中率
            SELECT 
                TEAM_NAME as team,
                COUNT(*) as three_attempts,
                SUM(SHOT_MADE) as three_made,
                ROUND(AVG(SHOT_MADE) * 100, 2) as three_percentage
            FROM nba_shots
            WHERE SHOT_TYPE = '3PT Field Goal'
            GROUP BY TEAM_NAME
            ORDER BY three_percentage DESC;
            
            -- 查询关键时刻（最后3分钟）投篮
            SELECT 
                PLAYER_NAME as player,
                COUNT(*) as clutch_attempts,
                SUM(SHOT_MADE) as clutch_made,
                ROUND(AVG(SHOT_MADE) * 100, 2) as clutch_percentage
            FROM nba_shots
            WHERE MINS_LEFT <= 3 AND QUARTER = 4
            GROUP BY PLAYER_NAME
            HAVING clutch_attempts >= 10
            ORDER BY clutch_percentage DESC
            LIMIT 10;
        """)
    
    def _get_database_schema(self) -> str:
        """获取数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取所有表的结构
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        ddl = []
        for table in tables:
            if table[0]:  # 排除系统表
                ddl.append(table[0])
        
        conn.close()
        return "\n".join(ddl)
    
    async def process_question(self, question: str) -> Dict[str, Any]:
        """处理用户问题"""
        try:
            # 1. 尝试从命令缓存获取 SQL
            cached_sql = self.command_cache.get(question)
            if cached_sql:
                sql = cached_sql
                print("Command cache hit, using cached SQL")
            else:
                # 生成 SQL
                sql = self.generate_sql(question)
                if sql:
                    # 缓存生成的 SQL
                    self.command_cache.set(question, sql)
                    print("Cached new SQL for command")
            
            if not sql:
                return {
                    "success": False,
                    "message": "无法生成有效的SQL查询"
                }
            
            print("Generated SQL:", sql)
            
            # 2. 尝试从查询缓存获取结果
            cached_result = self.query_cache.get(sql)
            if cached_result:
                return {
                    "success": True,
                    "data": cached_result
                }
            
            # 执行查询
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql)
            
            # 获取列名和结果
            columns = [description[0] for description in cursor.description]
            results = cursor.fetchall()
            
            # 生成解释
            try:
                explanation = self.generate_explanation(
                    question=question,
                    sql=sql,
                    results=results
                )
            except Exception as e:
                print("Error generating explanation:", e)
                if len(results) == 1 and len(results[0]) == 1:
                    explanation = f"查询结果是: {results[0][0]}"
                else:
                    explanation = f"查询到 {len(results)} 条记录"
            
            # 格式化结果
            formatted_results = []
            if len(columns) == 1 and len(results) == 1:
                formatted_results = results[0][0]
            else:
                for row in results:
                    formatted_results.append(dict(zip(columns, row)))
            
            response_data = {
                "message": explanation,
                "sql": sql,
                "results": formatted_results,
                "type": "single" if (len(columns) == 1 and len(results) == 1) else "table",
                "columns": columns
            }
            
            # 缓存查询结果
            self.query_cache.set(sql, None, response_data)
            
            return {
                "success": True,
                "data": response_data
            }
            
        except Exception as e:
            print("Error in process_question:", e)
            return {
                "success": False,
                "message": f"查询执行失败: {str(e)}"
            } 