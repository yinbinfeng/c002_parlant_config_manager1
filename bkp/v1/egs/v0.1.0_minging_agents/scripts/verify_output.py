#!/usr/bin/env python3
"""
Output Verification Script for Mining Agents v0.4.0

Verifies that all expected output files were generated correctly.
"""

import sys
from pathlib import Path


def verify_outputs():
    """Verify all output files exist and have content"""
    
    print("=" * 60)
    print("Mining Agents v0.4.0 - Output Verification")
    print("=" * 60)
    print()
    
    # Define expected output structure
    expected_files = {
        "step1": [
            "step1_clarification_questions.md",
            "step1_questions.json",
        ],
        "step2": [
            "step2_expert_analysis.md",
            "step2_customer_advocacy.md",
            "step2_debate_summary.md",
        ],
        "step3": [
            "step3_task_breakdown.md",
        ],
        "step4": [
            "step4_global_rules.md",
        ],
        "step5": [
            "step5_domain_configuration.md",
        ],
        "step6": [
            "step6_user_portrait_analysis.md",
        ],
        "step7": [
            "step7_quality_report.md",
        ],
        "step8": [
            "parlant_config.json",
            "parlant_config.yaml",
            "README.md",
        ]
    }
    
    output_base = Path("./output")
    
    if not output_base.exists():
        print("❌ Output directory does not exist!")
        print("   Please run the agents first to generate output.")
        return False
    
    all_passed = True
    total_files = 0
    existing_files = 0
    
    # Check each step
    for step, files in expected_files.items():
        step_dir = output_base / step
        print(f"Checking {step}/...")
        
        if not step_dir.exists():
            print(f"  ⚠️  Step {step} directory does not exist")
            all_passed = False
            continue
        
        for file in files:
            total_files += 1
            file_path = step_dir / file
            
            if file_path.exists():
                file_size = file_path.stat().st_size
                if file_size > 0:
                    print(f"  ✅ {file} ({file_size:,} bytes)")
                    existing_files += 1
                else:
                    print(f"  ⚠️  {file} (empty file)")
                    all_passed = False
            else:
                print(f"  ❌ {file} (not found)")
                all_passed = False
        
        print()
    
    # Summary
    print("=" * 60)
    print(f"Verification Summary:")
    print(f"  Total files expected: {total_files}")
    print(f"  Files found: {existing_files}")
    print(f"  Missing files: {total_files - existing_files}")
    print(f"  Success rate: {existing_files/total_files*100:.1f}%")
    print("=" * 60)
    print()
    
    if all_passed:
        print("✅ All output files verified successfully!")
        print()
        print("Next steps:")
        print("  1. Review output/step7/step7_quality_report.md for quality score")
        print("  2. Check output/step8/parlant_config.json for final configuration")
        print("  3. Read output/step8/README.md for deployment instructions")
        return True
    else:
        print("⚠️  Some files are missing or empty.")
        print("   You may need to re-run specific steps.")
        print()
        print("   Example: Run steps 1-3 only")
        print("   python -m src.mining_agents.main --business-desc \"...\" --start-step 1 --end-step 3")
        return False


if __name__ == "__main__":
    try:
        success = verify_outputs()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
