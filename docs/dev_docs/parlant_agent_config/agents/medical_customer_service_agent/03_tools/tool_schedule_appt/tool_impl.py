import asyncio
import uuid
from parlant.sdk import ToolContext, ToolResult

# 假设 p 是全局的 Parlant 工具注册器
p = None  # 实际使用时需要由框架注入

@p.tool
async def schedule_appt(
    context: ToolContext,
    department: str,
    doctor_name: str,
    appt_time: str,
    patient_name: str,
    patient_id_card: str
) -> ToolResult:
    """
    医疗客服 Agent 专属：预约挂号提交工具
    对应元信息 ID：medical_tool_schedule_appt
    """
    # 模拟调用医院 HIS 系统预约接口
    await asyncio.sleep(0.5)
    
    # 模拟生成预约结果
    appt_id = f"MED{uuid.uuid4().hex[:8].upper()}"
    
    return ToolResult(
        data={
            "appt_id": appt_id,
            "status": "success",
            "message": "预约成功",
            "department": department,
            "doctor_name": doctor_name,
            "appt_time": appt_time,
            "patient_name": patient_name
        }
    )
