from vanna.openai.openai_chat import OpenAI_Chat
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
import sqlite3
import os
from typing import Dict, Any

class VannaService(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)
        self.db_path = 'database.sqlite'
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
        
        # 添加业务文档
        self.train(documentation="""
            tasks 表存储了所有任务记录：
            - id: 任务ID
            - title: 任务标题
            - description: 任务描述
            - status: 任务状态 (pending/completed)
            - created_at: 创建时间
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
            # 生成 SQL
            sql = self.generate_sql(question)
            print("Generated SQL:", sql)
            if not sql:
                return {
                    "success": False,
                    "message": "无法生成有效的 SQL 查询"
                }
            
            # 清理生成的 SQL
            sql = sql.replace('```sql', '').replace('```', '').strip()
            
            # 执行查询
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql)
            columns = [description[0] for description in cursor.description]
            results = cursor.fetchall()
            print("Query Results:", results)
            conn.close()
            
            # 生成自然语言解释
            try:
                explanation = self.generate_response(
                    question=question,
                    sql=sql,
                    results=results
                )
            except Exception as e:
                print("Error generating explanation:", e)
                # 如果无法生成解释，使用默认解释
                if len(results) == 1 and len(results[0]) == 1:
                    explanation = f"查询结果是: {results[0][0]}"
                else:
                    explanation = f"查询到 {len(results)} 条记录"
            print("Generated Explanation:", explanation)
            
            # 格式化结果
            formatted_results = []
            for row in results:
                if len(columns) == 1:
                    formatted_results.append(row[0])
                else:
                    formatted_results.append(dict(zip(columns, row)))
            print("Formatted Results:", formatted_results)
            
            response = {
                "success": True,
                "data": {
                    "message": explanation,
                    "sql": sql,
                    "results": formatted_results
                }
            }
            print("Final Response:", response)
            return response
            
        except Exception as e:
            print("Error in process_question:", e)
            return {
                "success": False,
                "message": f"查询执行失败: {str(e)}"
            } 