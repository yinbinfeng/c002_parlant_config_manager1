#!/usr/bin/env python3
"""
启动 UI 的辅助脚本
"""
import subprocess
import sys
import time
import webbrowser

def main():
    print("正在启动 Streamlit UI...")
    
    # 启动 streamlit 服务
    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "test_ui_minimal.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # 等待服务启动
    time.sleep(3)
    
    print("UI 已启动！")
    print("请访问: http://localhost:8501")
    
    # 保持运行
    try:
        while True:
            output = process.stdout.readline()
            if output:
                print(output.strip())
            if process.poll() is not None:
                break
    except KeyboardInterrupt:
        print("\n正在停止 UI...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    main()
