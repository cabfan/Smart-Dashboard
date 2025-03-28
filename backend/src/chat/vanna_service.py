import os
import hashlib
import pandas as pd
from typing import Dict, Any, List
from ..cache.query_cache import QueryCache
from ..cache.command_cache import CommandCache
# from vanna.openai.openai_chat import OpenAI_Chat
# from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
from ..vanna.openai.openai_chat import OpenAI_Chat
from ..vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
from datetime import datetime
from decimal import Decimal

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
        # print("正在初始化 VannaService，配置信息:", config)
        print("正在初始化 VannaService 配置信息")
        if not config or 'api_key' not in config:
            raise ValueError("VannaService 需要 API 密钥")
        
        # 验证必需的配置项
        required_config = ['api_key', 'model', 'base_url']
        missing_config = [key for key in required_config if key not in config]
        print("检查必需配置。是否缺失:", missing_config if missing_config else "否")
        if missing_config:
            raise ValueError(f"缺少必需的配置项: {', '.join(missing_config)}")
        
        # 初始化父类
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)
        # 连接 MySQL 数据库
        mysql_config = config.get('mysql', {})
        self.connect_to_mysql(
            host=mysql_config.get('host'),
            dbname=mysql_config.get('database'),
            user=mysql_config.get('user'),
            password=mysql_config.get('password'),
            port=mysql_config.get('port', 3306)
        )
        # 设置缓存
        self.query_cache = QueryCache()  # 用于缓存SQL查询结果
        self.command_cache = CommandCache()  # 用于缓存自然语言到SQL的转换
    
    def _format_results(self, results_df):
        """格式化查询结果，处理时间戳等特殊类型"""
        def convert_value(obj):
            if pd.isna(obj):  # 处理 NaT 和其他空值
                return None
            if isinstance(obj, datetime):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(obj, Decimal):
                return float(obj)  # 将 Decimal 转换为 float
            return obj

        # 转换 DataFrame 为字典列表
        results = results_df.to_dict('records')
        
        # 处理每一行数据
        formatted_results = []
        for row in results:
            formatted_row = {k: convert_value(v) for k, v in row.items()}
            formatted_results.append(formatted_row)
            
        return formatted_results

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
                print("开始生成SQL...")
                try:
                    sql = self.generate_sql(question)
                    print(f"SQL生成成功: {sql}")
                    if sql:
                        self.command_cache.set(question, sql)
                        print("已缓存新的SQL命令")
                except Exception as e:
                    print(f"生成SQL时出错: {e}")
                    return {
                        "success": False,
                        "message": f"生成SQL失败: {str(e)}"
                    }
            
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
            
            # 3. 使用 Vanna 的 run_sql 执行查询
            try:
                print("开始执行SQL查询...")
                results_df = self.run_sql(sql)
                print(f"查询成功，返回 {len(results_df)} 条记录")
            except Exception as e:
                print(f"执行SQL查询时出错: {e}")
                return {
                    "success": False,
                    "message": f"SQL执行失败: {str(e)}"
                }

            # 格式化结果
            formatted_results = self._format_results(results_df)
            columns = results_df.columns.tolist()
            
            # 4. 生成结果解释
            try:
                print("开始生成结果解释...")
                explanation = self.generate_summary(
                    question=question,
                    df=results_df
                )
                print("结果解释生成成功")
            except Exception as e:
                print(f"生成解释时出错: {e}")
                explanation = f"查询到 {len(results_df)} 条记录"

            # 5. 构建响应数据
            response_data = {
                "message": explanation,
                "sql": sql,
                "results": formatted_results,
                "type": "single" if (len(columns) == 1 and len(formatted_results) == 1) else "table",
                "columns": columns
            }
            
            # 6. 缓存查询结果
            self.query_cache.set(sql, None, response_data)
            
            return {
                "success": True,
                "data": response_data
            }
            
        except Exception as e:
            print(f"处理问题时出错: {e}")
            import traceback
            traceback.print_exc()  # 打印完整的堆栈跟踪
            return {
                "success": False,
                "message": f"查询执行失败: {str(e)}"
            }

    def get_training_data(self) -> List[Dict[str, Any]]:
        """
        获取所有训练数据
        Returns:
            List[Dict[str, Any]]: 包含所有训练数据的列表，每条数据包含类型、内容、标题和备注
        """
        try:
       
            # 直接调用父类的 get_training_data 方法获取 DataFrame
            df = super().get_training_data()
            # 将 DataFrame 转换为所需的字典列表格式
            training_data = []
            
            for _, row in df.iterrows():
                # 使用安全的方式获取值，提供默认值防止 None 错误
                data = {
                    "id": row.get("id", "") if isinstance(row.get("id"), str) else "",
                    "type": row.get("training_data_type", "") if isinstance(row.get("training_data_type"), str) else "",
                    "content": row.get("content", "") if isinstance(row.get("content"), str) else "",
                }
                
                # 处理标题和备注，清理掉可能的 Form 对象字符串
                title = row.get("title", "")
                note = row.get("note", "")
                
                # 如果标题或备注包含 "annotation=NoneType"，说明是 Form 对象的字符串表示，需要清理
                if isinstance(title, str) and "annotation=NoneType" in title:
                    title = ""
                if isinstance(note, str) and "annotation=NoneType" in note:
                    note = ""
                    
                data["title"] = title
                data["note"] = note
                
                # 如果是问题-SQL对,添加问题字段
                if row.get("training_data_type") == "sql":
                    data["question"] = row.get("question", "") if isinstance(row.get("question"), str) else ""
                else:
                    data["question"] = ""  # 为非SQL类型也添加空的问题字段
                    
                training_data.append(data)
                
            return training_data
        except Exception as e:
            print(f"获取训练数据时出错: {e}")
            # 返回空列表而不是抛出异常，这样前端至少能显示空表格
            return []
    def add_training_data(self, data_type: str, content: str, question: str = None, title: str = "", note: str = "") -> str:
        """
        添加新的训练数据
        Args:
            data_type: 数据类型 (sql/documentation/ddl)
            content: 训练内容
            question: 如果是SQL类型，需要提供对应的问题
            title: 标题（可选）
            note: 备注（可选）
        Returns:
            str: 训练数据的ID
        """
        try:
            # 打印接收到的参数，用于调试
            print(f"接收到的训练数据参数: data_type={data_type}, content={content}, question={question}, title={title}, note={note}")
            
            # 确保所有参数都是正确的字符串类型
            data_type = str(data_type) if data_type is not None else ""
            content = str(content) if content is not None else ""
            question = str(question) if question is not None else None
            title = str(title) if title is not None else ""
            note = str(note) if note is not None else ""
            
            # 清理可能的 Form 对象字符串
            if isinstance(title, str) and "annotation=NoneType" in title:
                title = ""
            if isinstance(note, str) and "annotation=NoneType" in note:
                note = ""
            
            print(f"处理后的参数: data_type={data_type}, content={content}, question={question}, title={title}, note={note}")
            
            if data_type == "sql" and question:
                # 添加问题-SQL对
                return super().add_question_sql(question=question, sql=content, title=title, note=note)
            elif data_type == "ddl":
                # 添加DDL语句
                return super().add_ddl(ddl=content, title=title, note=note)
            elif data_type == "documentation":
                # 添加文档
                return super().add_documentation(documentation=content, title=title, note=note)
            else:
                raise ValueError("不支持的数据类型或缺少必要参数")
        except Exception as e:
            print(f"添加训练数据时出错: {e}")
            raise
    def remove_training_data(self, training_id: str) -> bool:
        """
        删除指定的训练数据
        Args:
            training_id: 训练数据的ID
        Returns:
            bool: 删除是否成功
        """
        try:
            return super().remove_training_data(training_id)
        except Exception as e:
            print(f"删除训练数据时出错: {e}")
            raise