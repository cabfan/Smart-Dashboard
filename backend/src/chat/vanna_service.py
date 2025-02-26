from vanna.openai.openai_chat import OpenAI_Chat
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
import sqlite3
import os
from typing import Dict, Any
from ..cache.query_cache import QueryCache
from ..cache.command_cache import CommandCache  # 新增命令缓存

class VannaService(ChromaDB_VectorStore, OpenAI_Chat):
    """
    Vanna服务类：集成了向量存储和OpenAI聊天功能，用于处理自然语言到SQL的转换
    继承自ChromaDB_VectorStore（向量存储）和OpenAI_Chat（OpenAI聊天）
    """
    def __init__(self, config=None):
        """
        初始化Vanna服务
        Args:
            config: 配置字典，必须包含api_key、model和base_url
        """
        print("正在初始化 VannaService，配置信息:", config)
        if not config or 'api_key' not in config:
            raise ValueError("VannaService 需要 API 密钥")
        
        # 验证必需的配置项
        required_config = ['api_key', 'model', 'base_url']
        missing_config = [key for key in required_config if key not in config]
        print("检查必需配置。缺失:", missing_config if missing_config else "无")
        if missing_config:
            raise ValueError(f"缺少必需的配置项: {', '.join(missing_config)}")
        
        # 初始化父类
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)
        
        # 设置数据库路径和缓存
        self.db_path = 'database.sqlite'
        self.query_cache = QueryCache()  # 用于缓存SQL查询结果
        self.command_cache = CommandCache()  # 用于缓存自然语言到SQL的转换
        
        # 初始化Vanna，包括训练数据
        self._init_vanna()
    
    def _init_vanna(self):
        """
        初始化Vanna服务，包括：
        1. 训练数据库表结构
        2. 训练示例SQL查询
        3. 加载NBA数据文档
        4. 训练业务文档
        """
        # 获取并训练数据库表结构
        ddl = self._get_database_schema()
        self.train(ddl=ddl)
        
        # 训练基础任务查询示例
        self.train(sql="""
            SELECT * FROM tasks 
            WHERE status = 'pending' 
            ORDER BY created_at DESC
        """)
        
        # 加载并训练NBA数据文档
        try:
            if os.path.exists('nba_docs.txt'):
                print("正在加载NBA文档...")
                with open('nba_docs.txt', 'r', encoding='utf-8') as f:
                    nba_docs = f.read()
                self.train(documentation=nba_docs)
                print("NBA文档训练成功")
            else:
                print("警告: 未找到nba_docs.txt")
        except Exception as e:
            print(f"训练NBA文档时出错: {e}")
        
        # 训练任务表业务文档
        self.train(documentation="""
            tasks 表存储了所有任务记录：
            - id: 任务ID
            - title: 任务标题
            - description: 任务描述
            - status: 任务状态 (pending/completed)
            - created_at: 创建时间
        """)
        
        # 训练NBA数据分析示例查询
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
        """
        获取数据库中所有表的DDL语句
        Returns:
            str: 所有表的建表语句，以换行符连接
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 从sqlite_master获取所有表的DDL
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        ddl = []
        for table in tables:
            if table[0]:  # 排除sqlite内部表
                ddl.append(table[0])
        
        conn.close()
        return "\n".join(ddl)
    
    async def process_question(self, question: str) -> Dict[str, Any]:
        """
        处理用户的自然语言问题
        
        处理流程：
        1. 检查命令缓存，尝试复用已有的SQL
        2. 如果缓存未命中，生成新的SQL
        3. 检查查询缓存，尝试复用查询结果
        4. 如果查询缓存未命中，执行SQL查询
        5. 生成结果解释
        6. 缓存查询结果
        
        Args:
            question: 用户的自然语言问题
            
        Returns:
            Dict包含：
            - success: 是否成功
            - data/message: 成功时返回数据，失败时返回错误信息
        """
        try:
            # 1. 尝试从命令缓存获取SQL
            cached_sql = self.command_cache.get(question)
            if cached_sql:
                sql = cached_sql
                print("命令缓存命中，使用缓存的SQL")
            else:
                # 生成新的SQL
                sql = self.generate_sql(question)
                if sql:
                    self.command_cache.set(question, sql)
                    print("已缓存新的SQL命令")
            
            if not sql:
                return {
                    "success": False,
                    "message": "无法生成有效的SQL查询"
                }
            
            print("生成的SQL:", sql)
            
            # 2. 尝试从查询缓存获取结果
            cached_result = self.query_cache.get(sql)
            if cached_result:
                return {
                    "success": True,
                    "data": cached_result
                }
            
            # 3. 执行查询并获取结果
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql)
            
            # 获取列名和查询结果
            columns = [description[0] for description in cursor.description]
            results = cursor.fetchall()
            
            # 4. 生成结果解释
            try:
                explanation = self.generate_explanation(
                    question=question,
                    sql=sql,
                    results=results
                )
            except Exception as e:
                print("生成解释时出错:", e)
                # 降级处理：使用简单的结果说明
                if len(results) == 1 and len(results[0]) == 1:
                    explanation = f"查询结果是: {results[0][0]}"
                else:
                    explanation = f"查询到 {len(results)} 条记录"
            
            # 5. 格式化查询结果
            formatted_results = []
            if len(columns) == 1 and len(results) == 1:
                formatted_results = results[0][0]  # 单值结果直接返回
            else:
                for row in results:
                    formatted_results.append(dict(zip(columns, row)))  # 将结果转换为字典列表
            
            # 6. 构建响应数据
            response_data = {
                "message": explanation,
                "sql": sql,
                "results": formatted_results,
                "type": "single" if (len(columns) == 1 and len(results) == 1) else "table",
                "columns": columns
            }
            
            # 7. 缓存查询结果
            self.query_cache.set(sql, None, response_data)
            
            return {
                "success": True,
                "data": response_data
            }
            
        except Exception as e:
            print("处理问题时出错:", e)
            return {
                "success": False,
                "message": f"查询执行失败: {str(e)}"
            }