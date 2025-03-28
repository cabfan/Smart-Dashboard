from fastapi import APIRouter, Form
from typing import Optional

router = APIRouter(prefix="/api/training", tags=["training"])

class TrainingRoute:
    def __init__(self, chat_manager):
        self.chat_manager = chat_manager

    async def list_training_data(self):
        try:
            training_data = self.chat_manager.vanna_service.get_training_data()
            return {
                "success": True,
                "data": training_data
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取训练数据失败: {str(e)}"
            }

    async def add_training_data(self, 
        data_type: str = Form(...),
        content: str = Form(...),
        question: Optional[str] = Form(None),
        title: Optional[str] = Form(""),  # 添加标题字段，默认为空字符串
        note: Optional[str] = Form("")    # 添加备注字段，默认为空字符串
    ):
        try:
            training_id = self.chat_manager.vanna_service.add_training_data(
                data_type=data_type,
                content=content,
                question=question,
                title=title,
                note=note
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

    async def delete_training_data(self, training_id: str):
        try:
            self.chat_manager.vanna_service.remove_training_data(training_id)
            return {
                "success": True,
                "message": "训练数据删除成功"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"删除训练数据失败: {str(e)}"
            }