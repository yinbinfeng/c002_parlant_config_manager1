import asyncio
import uuid
from parlant.sdk import ToolContext, ToolResult

# 假设 p 是全局的 Parlant 工具注册器
p = None  # 实际使用时需要由框架注入

@p.tool
async def book_flight(
    context: ToolContext,
    flight_no: str,
    seat_class: str,
    passenger_name: str,
    passenger_id_card: str,
    contact_phone: str
) -> ToolResult:
    """
    航空客服 Agent 专属：机票预订提交工具
    对应元信息 ID：airline_tool_book_flight
    """
    # 模拟调用航空公司订座系统接口
    await asyncio.sleep(0.5)
    
    # 模拟生成订单结果
    order_id = f"AIR{uuid.uuid4().hex[:8].upper()}"
    
    return ToolResult(
        data={
            "order_id": order_id,
            "status": "success",
            "message": "出票成功",
            "flight_no": flight_no,
            "seat_class": seat_class,
            "passenger_name": passenger_name
        }
    )
