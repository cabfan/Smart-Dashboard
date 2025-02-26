from fastapi import APIRouter
from datetime import datetime
import pytz

router = APIRouter(prefix="/api", tags=["system"])

class SystemRoute:
    @staticmethod
    async def get_current_time():
        try:
            tz = pytz.timezone('Asia/Shanghai')
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

    @staticmethod
    async def health_check():
        try:
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