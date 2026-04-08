#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据生成器
生成各种测试场景所需的数据
"""

import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta
import random


class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_business_descriptions(self):
        """生成多种业务描述测试数据"""
        business_cases = [
            {
                "name": "ecommerce_customer_service",
                "description": "电商客服 Agent，处理订单查询、退换货、商品咨询和投诉建议",
                "industry": "电子商务",
                "features": ["订单查询", "退换货", "商品咨询", "投诉处理"]
            },
            {
                "name": "banking_assistant",
                "description": "银行客服 Agent，处理账户查询、转账汇款、信用卡业务和理财咨询",
                "industry": "金融服务",
                "features": ["账户管理", "转账汇款", "信用卡", "理财产品"]
            },
            {
                "name": "travel_booking",
                "description": "旅游预订 Agent，处理机票预订、酒店预订、行程规划和退改签服务",
                "industry": "旅游服务",
                "features": ["机票预订", "酒店预订", "行程规划", "退改签"]
            },
            {
                "name": "healthcare_consultant",
                "description": "医疗健康咨询 Agent，提供科室导诊、医生排班查询、健康科普和预约挂号服务",
                "industry": "医疗健康",
                "features": ["科室导诊", "医生排班", "健康科普", "预约挂号"]
            },
            {
                "name": "education_advisor",
                "description": "教育咨询 Agent，提供课程推荐、学习规划、考试安排和证书查询服务",
                "industry": "教育培训",
                "features": ["课程推荐", "学习规划", "考试安排", "证书查询"]
            },
        ]
        
        output_file = self.output_dir / "business_descriptions.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(business_cases, f, indent=2, ensure_ascii=False)
        
        print(f"已生成业务描述测试数据：{output_file}")
        return business_cases
    
    def generate_mock_conversations(self, count=50):
        """生成模拟对话数据"""
        conversations = []
        
        user_types = ["新客户", "老客户", "VIP 客户", "投诉客户", "咨询客户"]
        issues = [
            "订单状态查询",
            "商品质量问题",
            "物流配送延迟",
            "退换货申请",
            "价格咨询",
            "促销活动询问",
            "支付方式问题",
            "发票开具",
        ]
        sentiments = ["满意", "中性", "不满", "愤怒", "焦急"]
        
        for i in range(count):
            conversation = {
                "id": f"conv_{i+1:04d}",
                "timestamp": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "user_type": random.choice(user_types),
                "issue_type": random.choice(issues),
                "sentiment": random.choice(sentiments),
                "turns": random.randint(3, 15),
                "resolution": random.choice(["已解决", "部分解决", "未解决", "升级处理"]),
                "satisfaction_score": random.randint(1, 5),
            }
            conversations.append(conversation)
        
        output_file = self.output_dir / "mock_conversations.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(conversations, f, indent=2, ensure_ascii=False)
        
        print(f"已生成模拟对话数据：{output_file} ({count}条)")
        return conversations
    
    def generate_user_portraits(self, count=20):
        """生成用户画像数据"""
        portraits = []
        
        age_groups = ["18-25", "26-35", "36-45", "46-55", "55+"]
        regions = ["一线城市", "二线城市", "三线城市", "农村地区"]
        preferences = [
            ["价格敏感", "追求性价比"],
            ["品质优先", "注重品牌"],
            ["服务导向", "重视体验"],
            ["效率至上", "快速解决"],
        ]
        
        for i in range(count):
            portrait = {
                "id": f"user_{i+1:03d}",
                "age_group": random.choice(age_groups),
                "region": random.choice(regions),
                "purchase_frequency": random.choice(["高频", "中频", "低频"]),
                "avg_order_value": random.randint(100, 5000),
                "preferred_categories": random.sample(
                    ["数码", "服装", "家居", "食品", "美妆", "运动"],
                    k=random.randint(1, 3)
                ),
                "preferences": random.choice(preferences),
                "common_issues": random.sample(issues := [
                    "物流查询", "退换货", "商品咨询", "售后维修", "发票问题"
                ], k=random.randint(1, 3)),
                "communication_style": random.choice([
                    "简洁直接", "详细询问", "情绪化", "理性分析"
                ]),
            }
            portraits.append(portrait)
        
        output_file = self.output_dir / "user_portraits.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(portraits, f, indent=2, ensure_ascii=False)
        
        print(f"已生成用户画像数据：{output_file} ({count}个)")
        return portraits
    
    def generate_domain_knowledge(self, industry="ecommerce"):
        """生成领域知识库"""
        knowledge_bases = {
            "ecommerce": {
                "terms": {
                    "SKU": "库存量单位，指商品的唯一标识",
                    "UV": "独立访客数，统计访问店铺的独立用户数",
                    "PV": "页面浏览量，用户每打开或刷新一次页面就算一次",
                    "转化率": "访客中完成购买的比例",
                    "客单价": "每个顾客平均交易金额",
                    "DSR": "卖家服务评级系统",
                },
                "policies": {
                    "7 天无理由退换": "自签收次日起 7 天内，商品完好可申请退换",
                    "运费险": "退货时可获赔首重运费的保险服务",
                    "价保服务": "购买后一定期限内降价可补差价",
                },
                "workflows": {
                    "退换货流程": [
                        "用户提交申请",
                        "客服审核",
                        "用户寄回商品",
                        "仓库验货",
                        "退款/换货"
                    ],
                    "投诉处理流程": [
                        "接收投诉",
                        "记录详情",
                        "调查核实",
                        "提出方案",
                        "执行补偿",
                        "回访反馈"
                    ]
                }
            },
            "banking": {
                "terms": {
                    "活期存款": "随时可以存取的存款方式",
                    "定期存款": "约定存期，到期支取本息的存款",
                    "理财": "银行发行的投资产品",
                    "信用卡": "先消费后还款的信用支付工具",
                },
                "policies": {
                    "挂失政策": "卡片丢失可立即挂失，48 小时内到网点办理正式挂失",
                    "转账限额": "单笔转账限额根据认证方式不同从 1 万到 500 万不等",
                },
                "workflows": {
                    "开户流程": [
                        "身份验证",
                        "填写申请表",
                        "设置密码",
                        "领取卡片",
                        "激活账户"
                    ]
                }
            }
        }
        
        knowledge = knowledge_bases.get(industry, knowledge_bases["ecommerce"])
        
        output_file = self.output_dir / f"{industry}_knowledge.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(knowledge, f, indent=2, ensure_ascii=False)
        
        print(f"已生成领域知识数据：{output_file}")
        return knowledge
    
    def generate_quality_check_scenarios(self):
        """生成质量检查场景"""
        scenarios = [
            {
                "name": "完整配置测试",
                "step_outputs": {f"step{i}": {"data": f"data_{i}"} for i in range(1, 9)},
                "expected_score_range": (80, 100),
                "expected_level": "Excellent/Good"
            },
            {
                "name": "缺少 Step 数据",
                "step_outputs": {f"step{i}": {"data": f"data_{i}"} for i in range(1, 6)},
                "expected_score_range": (40, 60),
                "expected_level": "Needs Improvement"
            },
            {
                "name": "空配置测试",
                "step_outputs": {},
                "expected_score_range": (0, 20),
                "expected_level": "Failed"
            },
            {
                "name": "部分数据无效",
                "step_outputs": {
                    **{f"step{i}": {"data": f"data_{i}"} for i in range(1, 5)},
                    "step5": None,
                    "step6": {},
                    "step7": {"invalid": True},
                    "step8": {"incomplete": True}
                },
                "expected_score_range": (30, 50),
                "expected_level": "Needs Improvement"
            }
        ]
        
        output_file = self.output_dir / "quality_check_scenarios.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(scenarios, f, indent=2, ensure_ascii=False)
        
        print(f"已生成质量检查场景：{output_file}")
        return scenarios
    
    def generate_excel_sample(self):
        """生成 Excel 示例文件（CSV 格式）"""
        try:
            import pandas as pd
            
            # 生成示例数据
            data = {
                "对话 ID": [f"conv_{i:04d}" for i in range(1, 101)],
                "日期": [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(100)],
                "用户类型": [random.choice(["新客户", "老客户", "VIP"]) for _ in range(100)],
                "问题类型": [random.choice(["订单查询", "退换货", "商品咨询", "投诉"]) for _ in range(100)],
                "满意度": [random.randint(1, 5) for _ in range(100)],
                "处理时长 (分钟)": [random.randint(5, 60) for _ in range(100)],
                "是否解决": [random.choice(["是", "否"]) for _ in range(100)],
            }
            
            df = pd.DataFrame(data)
            
            csv_file = self.output_dir / "sample_conversations.csv"
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            
            print(f"已生成 Excel 示例数据 (CSV): {csv_file}")
            return str(csv_file)
            
        except ImportError:
            print("⚠️  pandas 未安装，跳过 Excel 数据生成")
            return None
    
    def generate_all(self):
        """生成所有测试数据"""
        print("="*80)
        print("生成测试数据")
        print("="*80)
        
        self.generate_business_descriptions()
        self.generate_mock_conversations(50)
        self.generate_user_portraits(20)
        self.generate_domain_knowledge("ecommerce")
        self.generate_quality_check_scenarios()
        self.generate_excel_sample()
        
        print("\n✅ 所有测试数据生成完成")
        print(f"输出目录：{self.output_dir}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="生成测试数据")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./test_data",
        help="输出目录"
    )
    
    args = parser.parse_args()
    
    generator = TestDataGenerator(Path(args.output_dir))
    generator.generate_all()


if __name__ == "__main__":
    main()
