import asyncio
from parlant.sdk import ToolContext, ToolResult

# 假设 p 是全局的 Parlant 工具注册器
p = None  # 实际使用时需要由框架注入

@p.tool
async def risk_assessment(
    context: ToolContext,
    age: int,
    occupation: str,
    annual_income: float = 0,
    has_social_insurance: bool = True,
    family_burden: str = ""
) -> ToolResult:
    """
    保险销售 Agent专属：风险评估与保额计算工具
    对应元信息 ID：insurance_tool_risk_assessment
    """
    # 模拟调用保险精算模型
    await asyncio.sleep(0.3)
    
    # 简化版风险缺口计算逻辑
    base_coverage = 500000  # 基础保额 50 万
    
    # 根据年龄调整
    if age < 30:
        age_factor = 1.0
    elif age < 45:
        age_factor = 1.2
    else:
        age_factor = 1.5
    
    # 根据是否有社保调整
    social_factor = 0.8 if has_social_insurance else 1.3
    
    # 根据家庭负担调整
    burden_factor = 1.0
    if "房贷" in family_burden or "车贷" in family_burden:
        burden_factor += 0.3
    if "小孩" in family_burden or "子女" in family_burden:
        burden_factor += 0.2
    if "老人" in family_burden or "赡养" in family_burden:
        burden_factor += 0.2
    
    # 计算推荐保额
    recommended_life = int(base_coverage * age_factor * social_factor * burden_factor)
    recommended_critical = int(recommended_life * 0.6)  # 重疾保额通常为寿险的 60%
    recommended_medical = 1000000  # 医疗险固定 100 万
    
    # 计算风险缺口
    risk_gap = recommended_life - (annual_income * 0.5 if annual_income > 0 else 0)
    
    return ToolResult(
        data={
            "risk_gap": max(0, risk_gap),
            "recommended_coverage": {
                "critical_illness": recommended_critical,
                "medical": recommended_medical,
                "life": recommended_life
            },
            "recommendation_reason": f"根据您的年龄、职业和家庭责任，建议配置重疾险{recommended_critical/10000:.0f}万、医疗险{recommended_medical/10000:.0f}万、寿险{recommended_life/10000:.0f}万的综合保障方案"
        },
        guidelines=[
            {"action": "优先推荐消费型重疾险，保费更低保障更高", "priority": 4},
            {"action": "强调医疗险作为社保补充的重要性", "priority": 3}
        ]
    )
