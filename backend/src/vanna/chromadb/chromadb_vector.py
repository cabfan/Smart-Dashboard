import json
from typing import List

import chromadb
import pandas as pd
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from ..base import VannaBase
from ..utils import deterministic_uuid

from FlagEmbedding import BGEM3FlagModel

# zpaz 2025-03-24 自定义嵌入函数类
# 创建 BGE-M3 模型实例
bge_m3_model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
class BGEM3EmbeddingFunction:
    def __call__(self, input):  # 修改参数名为 input 而不是 texts
        if not input:
            return []
        # 使用 BGE-M3 模型生成嵌入向量
        embeddings = bge_m3_model.encode(input, batch_size=12, max_length=8192)['dense_vecs']
        return embeddings.tolist()

# default_ef = embedding_functions.DefaultEmbeddingFunction()
# 使用自定义的 BGE-M3 嵌入函数
default_ef = BGEM3EmbeddingFunction()

class ChromaDB_VectorStore(VannaBase):
    def __init__(self, config=None):
        VannaBase.__init__(self, config=config)
        if config is None:
            config = {}

        path = config.get("path", ".")
        self.embedding_function = config.get("embedding_function", default_ef)
        curr_client = config.get("client", "persistent")
        collection_metadata = config.get("collection_metadata", None)
        self.n_results_sql = config.get("n_results_sql", config.get("n_results", 10))
        self.n_results_documentation = config.get("n_results_documentation", config.get("n_results", 10))
        self.n_results_ddl = config.get("n_results_ddl", config.get("n_results", 10))

        if curr_client == "persistent":
            self.chroma_client = chromadb.PersistentClient(
                path=path, settings=Settings(anonymized_telemetry=False)
            )
        elif curr_client == "in-memory":
            self.chroma_client = chromadb.EphemeralClient(
                settings=Settings(anonymized_telemetry=False)
            )
        elif isinstance(curr_client, chromadb.api.client.Client):
            # allow providing client directly
            self.chroma_client = curr_client
        else:
            raise ValueError(f"Unsupported client was set in config: {curr_client}")

        self.documentation_collection = self.chroma_client.get_or_create_collection(
            name="documentation",
            embedding_function=self.embedding_function,
            metadata=collection_metadata,
        )
        self.ddl_collection = self.chroma_client.get_or_create_collection(
            name="ddl",
            embedding_function=self.embedding_function,
            metadata=collection_metadata,
        )
        self.sql_collection = self.chroma_client.get_or_create_collection(
            name="sql",
            embedding_function=self.embedding_function,
            metadata=collection_metadata,
        )

    def generate_embedding(self, data: str, **kwargs) -> List[float]:
        embedding = self.embedding_function([data])
        if len(embedding) == 1:
            return embedding[0]
        return embedding

    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        # 打印接收到的参数，用于调试
        print(f"add_question_sql 接收到的参数: question={question}, sql={sql}, kwargs={kwargs}")
        
        # 提取标题和备注，确保它们是简单的字符串类型
        title = str(kwargs.get("title", "")) if kwargs.get("title") is not None else ""
        note = str(kwargs.get("note", "")) if kwargs.get("note") is not None else ""
        
        # 清理可能的 Form 对象字符串
        if "annotation=NoneType" in title:
            title = ""
        if "annotation=NoneType" in note:
            note = ""
        
        print(f"处理后的元数据: title={title}, note={note}")
        
        question_sql_json = json.dumps(
            {
                "question": question,
                "sql": sql,
                "title": title,
                "note": note,
            },
            ensure_ascii=False,
        )
        id = deterministic_uuid(question_sql_json) + "-sql"
        
        # 添加元数据
        metadata = {
            "title": title,
            "note": note,
        }
        
        self.sql_collection.add(
            documents=question_sql_json,
            embeddings=self.generate_embedding(question_sql_json),
            ids=id,
            metadatas=metadata,
        )
    
        return id

    def add_ddl(self, ddl: str, **kwargs) -> str:
        # 提取标题和备注，确保它们是字符串类型
        title = str(kwargs.get("title", "")) if kwargs.get("title") is not None else ""
        note = str(kwargs.get("note", "")) if kwargs.get("note") is not None else ""
        
        id = deterministic_uuid(ddl) + "-ddl"
        
        # 添加元数据
        metadata = {
            "title": title,
            "note": note,
        }
        
        self.ddl_collection.add(
            documents=ddl,
            embeddings=self.generate_embedding(ddl),
            ids=id,
            metadatas=metadata,
        )
        return id

    def add_documentation(self, documentation: str, **kwargs) -> str:
        # 提取标题和备注，确保它们是字符串类型
        title = str(kwargs.get("title", "")) if kwargs.get("title") is not None else ""
        note = str(kwargs.get("note", "")) if kwargs.get("note") is not None else ""
        
        id = deterministic_uuid(documentation) + "-doc"
        
        # 添加元数据
        metadata = {
            "title": title,
            "note": note,
        }
        
        self.documentation_collection.add(
            documents=documentation,
            embeddings=self.generate_embedding(documentation),
            ids=id,
            metadatas=metadata,
        )
        return id

    def get_training_data(self, **kwargs) -> pd.DataFrame:
        print("开始获取训练数据...")
        sql_data = self.sql_collection.get()
        print(f"获取到的 SQL 数据: {sql_data}")
    
        df = pd.DataFrame()
        
        if sql_data is not None and "documents" in sql_data and len(sql_data["documents"]) > 0:
            try:
                # 安全地提取文档
                documents = []
                for doc in sql_data["documents"]:
                    try:
                        documents.append(json.loads(doc))
                    except Exception as e:
                        print(f"解析 SQL 文档时出错: {e}")
                        documents.append({})
                
                ids = sql_data["ids"]
                # 安全地获取元数据
                metadatas = sql_data.get("metadatas", [{"title": "", "note": ""} for _ in ids])
                
                # 创建数据框
                data = {
                    "id": ids,
                    "question": [doc.get("question", "") for doc in documents],
                    "content": [doc.get("sql", "") for doc in documents],
                    "title": [meta.get("title", "") if meta else "" for meta in metadatas],
                    "note": [meta.get("note", "") if meta else "" for meta in metadatas],
                }
                
                df_sql = pd.DataFrame(data)
                df_sql["training_data_type"] = "sql"
                df = pd.concat([df, df_sql])
                
                print(f"处理后的 SQL 数据框: {df_sql}")
            except Exception as e:
                print(f"处理 SQL 数据时出错: {e}")

        # 类似地修改 ddl_data 和 doc_data 的处理
        ddl_data = self.ddl_collection.get()

        if ddl_data is not None:
            # Extract the documents and ids
            documents = [doc for doc in ddl_data["documents"]]
            ids = ddl_data["ids"]
            metadatas = ddl_data.get("metadatas", [{"title": "", "note": ""} for _ in ids])

            # Create a DataFrame
            df_ddl = pd.DataFrame(
                {
                    "id": ids,
                    "question": [None for doc in documents],
                    "content": [doc for doc in documents],
                    "title": [meta.get("title", "") for meta in metadatas],
                    "note": [meta.get("note", "") for meta in metadatas],
                }
            )

            df_ddl["training_data_type"] = "ddl"

            df = pd.concat([df, df_ddl])

        doc_data = self.documentation_collection.get()

        if doc_data is not None:
            # Extract the documents and ids
            documents = [doc for doc in doc_data["documents"]]
            ids = doc_data["ids"]
            metadatas = doc_data.get("metadatas", [{"title": "", "note": ""} for _ in ids])

            # Create a DataFrame
            df_doc = pd.DataFrame(
                {
                    "id": ids,
                    "question": [None for doc in documents],
                    "content": [doc for doc in documents],
                    "title": [meta.get("title", "") for meta in metadatas],
                    "note": [meta.get("note", "") for meta in metadatas],
                }
            )

            df_doc["training_data_type"] = "documentation"

            df = pd.concat([df, df_doc])

        print(f"最终返回的数据框: {df}")
        return df

    def remove_training_data(self, id: str, **kwargs) -> bool:
        if id.endswith("-sql"):
            self.sql_collection.delete(ids=id)
            return True
        elif id.endswith("-ddl"):
            self.ddl_collection.delete(ids=id)
            return True
        elif id.endswith("-doc"):
            self.documentation_collection.delete(ids=id)
            return True
        else:
            return False

    def remove_collection(self, collection_name: str) -> bool:
        """
        This function can reset the collection to empty state.

        Args:
            collection_name (str): sql or ddl or documentation

        Returns:
            bool: True if collection is deleted, False otherwise
        """
        if collection_name == "sql":
            self.chroma_client.delete_collection(name="sql")
            self.sql_collection = self.chroma_client.get_or_create_collection(
                name="sql", embedding_function=self.embedding_function
            )
            return True
        elif collection_name == "ddl":
            self.chroma_client.delete_collection(name="ddl")
            self.ddl_collection = self.chroma_client.get_or_create_collection(
                name="ddl", embedding_function=self.embedding_function
            )
            return True
        elif collection_name == "documentation":
            self.chroma_client.delete_collection(name="documentation")
            self.documentation_collection = self.chroma_client.get_or_create_collection(
                name="documentation", embedding_function=self.embedding_function
            )
            return True
        else:
            return False

    @staticmethod
    def _extract_documents(query_results) -> list:
        """
        Static method to extract the documents from the results of a query.

        Args:
            query_results (pd.DataFrame): The dataframe to use.

        Returns:
            List[str] or None: The extracted documents, or an empty list or
            single document if an error occurred.
        """
        if query_results is None:
            return []

        if "documents" in query_results:
            documents = query_results["documents"]

            if len(documents) == 1 and isinstance(documents[0], list):
                try:
                    documents = [json.loads(doc) for doc in documents[0]]
                except Exception as e:
                    print(f"处理问题时出错: {e}")
                    return documents[0]

            return documents
        return []

    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        min_similarity = kwargs.get("min_similarity", 0.9)
        print(f"开始召回相关SQL: question={question}")
        results = self.sql_collection.query(
            query_texts=[question],
            n_results=self.n_results_sql
        )
        # 添加过滤逻辑
        filtered_results = {"documents": []}
        if "documents" in results and "distances" in results:
            filtered_documents = []
            for i, distance in enumerate(results['distances'][0]):  # 获取第一个查询的距离结果
                if distance < min_similarity:  # 比较单个浮点数
                    if i < len(results['documents'][0]):  # 确保索引有效
                        filtered_documents.append(results['documents'][0][i])
            
            # 创建一个新的结果字典，保持原始结构
            filtered_results = {"documents": [filtered_documents]}
            print(f"过滤后的SQL结果: filtered_results={filtered_results}")
            return ChromaDB_VectorStore._extract_documents(filtered_results)
        
        return ChromaDB_VectorStore._extract_documents(results)

    def get_related_ddl(self, question: str, **kwargs) -> list:
        min_similarity = kwargs.get("min_similarity", 0.9)
        print(f"开始召回相关 DDL: question={question}")
        results = self.ddl_collection.query(
            query_texts=[question],
            n_results=self.n_results_ddl
        )
        # 添加过滤逻辑
        filtered_results = {"documents": []}
        if "documents" in results and "distances" in results:
            filtered_documents = []
            for i, distance in enumerate(results['distances'][0]):  # 获取第一个查询的距离结果
                if distance < min_similarity:  # 比较单个浮点数
                    if i < len(results['documents'][0]):  # 确保索引有效
                        filtered_documents.append(results['documents'][0][i])
            
            # 创建一个新的结果字典，保持原始结构
            filtered_results = {"documents": [filtered_documents]}
            print(f"过滤后的DDL结果: filtered_results={filtered_results}")
            return ChromaDB_VectorStore._extract_documents(filtered_results)
        
        return ChromaDB_VectorStore._extract_documents(results)

    def get_related_documentation(self, question: str, **kwargs) -> list:
        min_similarity = kwargs.get("min_similarity", 0.9)
        print(f"开始召回相关文档: question={question}")
        results = self.documentation_collection.query(
            query_texts=[question],
            n_results=self.n_results_documentation
        )
        
        # 修复过滤逻辑，确保返回正确的数据结构
        if "documents" in results and "distances" in results:
            filtered_documents = []
            for i, distance in enumerate(results['distances'][0]):  # 获取第一个查询的距离结果
                if distance < min_similarity:  # 比较单个浮点数
                    if i < len(results['documents'][0]):  # 确保索引有效
                        filtered_documents.append(results['documents'][0][i])
            
            # 创建一个新的结果字典，保持原始结构
            filtered_results = {"documents": [filtered_documents]}
            print(f"召回相关文档并过滤完成: filtered_results={filtered_results}")
            return ChromaDB_VectorStore._extract_documents(filtered_results)
        
        return ChromaDB_VectorStore._extract_documents(results)
