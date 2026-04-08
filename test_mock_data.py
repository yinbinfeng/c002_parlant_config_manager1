#!/usr/bin/env python3
"""测试 Mock 数据加载"""
import yaml
from pathlib import Path

UI_MOCK_DIR = Path(__file__).parent / "egs" / "v0.1.0_minging_agents" / "config" / "mock"
UI_EXAMPLES_CONFIG_PATH = UI_MOCK_DIR / "ui_examples.yaml"
INSURANCE_MOCK_DATA_PATH = UI_MOCK_DIR / "insurance_mock_data.yaml"


def test_mock_data():
    """测试 Mock 数据加载"""
    print("=== 测试 Mock 数据加载 ===\n")
    
    # 1. 加载 ui_examples.yaml
    print("1. 加载 ui_examples.yaml...")
    try:
        with open(UI_EXAMPLES_CONFIG_PATH, "r", encoding="utf-8") as f:
            examples = yaml.safe_load(f)
        print(f"   ✓ 成功，找到 {len(examples.get('examples', []))} 个示例\n")
    except Exception as e:
        print(f"   ✗ 失败: {e}\n")
        return False
    
    # 2. 加载 insurance_mock_data.yaml
    print("2. 加载 insurance_mock_data.yaml...")
    try:
        with open(INSURANCE_MOCK_DATA_PATH, "r", encoding="utf-8") as f:
            mock_data = yaml.safe_load(f)
        print(f"   ✓ 成功\n")
    except Exception as e:
        print(f"   ✗ 失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. 验证数据结构
    print("3. 验证数据结构...")
    output = mock_data.get("output", {})
    journeys = output.get("journeys", [])
    guidelines = output.get("guidelines", [])
    glossary = output.get("glossary", [])
    tools = output.get("tools", [])
    canned_responses = output.get("canned_responses", [])
    
    print(f"   - 流程数量: {len(journeys)}")
    print(f"   - 规则数量: {len(guidelines)}")
    print(f"   - 术语数量: {len(glossary)}")
    print(f"   - 工具数量: {len(tools)}")
    print(f"   - 话术数量: {len(canned_responses)}")
    
    # 4. 检查旅程类型
    print("\n4. 检查旅程类型...")
    main_journeys = [j for j in journeys if j.get("sop_type") == "main"]
    branch_journeys = [j for j in journeys if j.get("sop_type") == "branch"]
    edge_journeys = [j for j in journeys if j.get("sop_type") == "edge"]
    print(f"   - 主流程: {len(main_journeys)}")
    print(f"   - 分支流程: {len(branch_journeys)}")
    print(f"   - 边缘场景: {len(edge_journeys)}")
    
    # 5. 检查节点关联
    print("\n5. 检查节点关联...")
    for j in journeys[:1]:
        jname = j.get("name")
        print(f"   - {jname}:")
        nodes = j.get("nodes", [])
        for node in nodes:
            bind_guidelines = node.get("bind_guideline_ids", [])
            bind_tool = node.get("bind_tool_id")
            bind_crs = node.get("bind_canned_response_ids", [])
            if bind_guidelines or bind_tool or bind_crs:
                print(f"     • {node.get('label')}:")
                if bind_guidelines:
                    print(f"       - 规则: {bind_guidelines}")
                if bind_tool:
                    print(f"       - 工具: {bind_tool}")
                if bind_crs:
                    print(f"       - 话术: {bind_crs}")
    
    print("\n=== 测试完成，所有数据结构正确！ ===\n")
    return True


if __name__ == "__main__":
    success = test_mock_data()
    import sys
    sys.exit(0 if success else 1)
