import asyncio
from parlant.sdk import ToolContext, ToolResult

# 假设 p 是全局的 Parlant 工具注册器
p = None  # 实际使用时需要由框架注入

@p.tool
async def load_flight_deals(
    context: ToolContext,
    departure: str,
    arrival: str,
    travel_date: str,
    direct_only: bool = False
) -> ToolResult:
    """
    航空客服 Agent 专属：航班查询工具
    对应元信息 ID：airline_tool_load_flight_deals
    """
    # 模拟调用航空公司 GDS 系统接口
    await asyncio.sleep(0.3)
    
    # 模拟返回航班数据
    flights = [
        {
            "flight_no": "CA1234",
            "airline": "中国国际航空",
            "depart_time": "08:00",
            "arrive_time": "11:00",
            "seats": [
                {"class": "经济舱", "price": 1200},
                {"class": "商务舱", "price": 3500}
            ]
        },
        {
            "flight_no": "MU5678",
            "airline": "东方航空",
            "depart_time": "14:30",
            "arrive_time": "17:30",
            "seats": [
                {"class": "经济舱", "price": 1100},
                {"class": "商务舱", "price": 3200}
            ]
        }
    ]
    
    # 如果仅查询直飞，过滤掉转机航班（此处简化处理）
    if direct_only:
        flights = [f for f in flights if "经停" not in f["flight_no"]]
    
    return ToolResult(
        data=flights,
        guidelines=[
            {"action": "优先展示价格更低、时间更合适的航班", "priority": 4}
        ]
    )
