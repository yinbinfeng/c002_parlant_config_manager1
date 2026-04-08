import asyncio
from parlant.sdk import ToolContext, ToolResult

# 假设 p 是全局的 Parlant 工具注册器
p = None  # 实际使用时需要由框架注入

@p.tool
async def get_upcoming_slots(
    context: ToolContext, 
    department: str, 
    doctor_name: str = ""
) -> ToolResult:
    """
    医疗客服 Agent 专属：门诊可预约时间查询工具
    对应元信息 ID：medical_tool_get_upcoming_slots
    """
    # 模拟调用医院 HIS 系统接口
    await asyncio.sleep(0.2)
    
    # 模拟返回可预约数据
    doctors = [
        {
            "name": "张建国",
            "title": "主任医师",
            "available_slots": [
                {"date": "2026-03-10", "time": "09:00"},
                {"date": "2026-03-10", "time": "10:30"},
                {"date": "2026-03-11", "time": "14:00"}
            ]
        },
        {
            "name": "李梅",
            "title": "副主任医师",
            "available_slots": [
                {"date": "2026-03-10", "time": "11:00"},
                {"date": "2026-03-12", "time": "09:30"},
                {"date": "2026-03-12", "time": "15:00"}
            ]
        }
    ]
    
    # 按医生姓名过滤数据
    if doctor_name:
        doctors = [d for d in doctors if doctor_name in d["name"]]
    
    return ToolResult(
        data=doctors,
        guidelines=[
            {"action": "优先展示职称更高、可预约时段更多的医生", "priority": 4}
        ]
    )
