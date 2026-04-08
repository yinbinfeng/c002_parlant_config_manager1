import asyncio
from parlant.sdk import ToolContext, ToolResult

# 假设 p 是全局的 Parlant 工具注册器
p = None  # 实际使用时需要由框架注入

@p.tool
async def calculate_premium(
    context: ToolContext,
    product_name: str,
    coverage_amount: float,
    payment_term: int,
    coverage_period: int,
    age: int,
    gender: str
) -> ToolResult:
    """
    保险销售 Agent专属：保费计算工具
    对应元信息 ID：insurance_tool_calculate_premium
    """
    # 模拟调用保险公司精算模型
    await asyncio.sleep(0.3)
    
    # 简化版保费计算逻辑
    # 基础费率：每 1 万保额的年缴保费
    base_rate_map = {
        "重疾险": 0.0003,  # 每 1 万保额 3 元/年
        "医疗险": 0.0001,  # 每 1 万保额 1 元/年
        "寿险": 0.0002,    # 每 1 万保额 2 元/年
        "意外险": 0.00005  # 每 1 万保额 0.5 元/年
    }
    
    # 根据产品名称判断保险类型
    insurance_type = "重疾险"  # 默认
    if "医疗" in product_name:
        insurance_type = "医疗险"
    elif "寿险" in product_name:
        insurance_type = "寿险"
    elif "意外" in product_name:
        insurance_type = "意外险"
    
    base_rate = base_rate_map.get(insurance_type, 0.0003)
    
    # 年龄系数：年龄越大，保费越高
    if age < 30:
        age_factor = 0.8
    elif age < 40:
        age_factor = 1.0
    elif age < 50:
        age_factor = 1.3
    else:
        age_factor = 1.8
    
    # 性别系数：男性某些险种费率更高
    gender_factor = 1.0
    if gender == "男":
        if insurance_type in ["重疾险", "医疗险"]:
            gender_factor = 1.1
        elif insurance_type == "寿险":
            gender_factor = 1.15
    else:  # 女性
        if insurance_type == "重疾险":
            gender_factor = 0.95
    
    # 缴费年限系数：缴费期越长，年缴保费略低
    payment_term_factor = 1.0
    if payment_term >= 30:
        payment_term_factor = 0.95
    elif payment_term >= 20:
        payment_term_factor = 1.0
    else:
        payment_term_factor = 1.05
    
    # 计算基础保费
    base_premium = coverage_amount * base_rate * age_factor * gender_factor * payment_term_factor
    
    # 年缴保费
    annual_premium = round(base_premium, 2)
    
    # 月缴保费（年缴保费 / 12，略有上浮）
    monthly_premium = round(annual_premium / 12 * 1.05, 2)
    
    # 总保费
    total_premium = round(annual_premium * payment_term, 2)
    
    calculation_note = (
        f"保费计算说明：\n"
        f"- 保险产品：{product_name}（{insurance_type}）\n"
        f"- 保额：{coverage_amount/10000:.0f}万元\n"
        f"- 缴费年限：{payment_term}年\n"
        f"- 保障期限：{coverage_period}年\n"
        f"- 被保险人：{age}岁，{gender}\n"
        f"- 基础费率：{base_rate*10000:.1f}元/万保额/年\n"
        f"- 年龄系数：{age_factor:.1f}（年龄越大费率越高）\n"
        f"- 性别系数：{gender_factor:.2f}（不同性别发病率差异）\n"
        f"- 缴费年期系数：{payment_term_factor:.2f}（长期缴费略有优惠）"
    )
    
    return ToolResult(
        data={
            "annual_premium": annual_premium,
            "monthly_premium": monthly_premium,
            "total_premium": total_premium,
            "premium_breakdown": {
                "base_premium": round(base_premium, 2),
                "age_factor": age_factor,
                "gender_factor": gender_factor
            },
            "calculation_note": calculation_note
        },
        guidelines=[
            {
                "action": "清晰展示保费计算结果，包含年缴、月缴、总保费，并解释保费构成与影响因素",
                "priority": 4
            },
            {
                "action": "若用户觉得保费过高，可推荐调整保额、延长缴费年限或选择保障期限更短的方案",
                "priority": 5
            }
        ]
    )
