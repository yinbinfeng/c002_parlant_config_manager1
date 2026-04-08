import streamlit as st

class AutomatedTestUI:
    def __init__(self):
        pass
    
    def run(self):
        st.set_page_config(
            page_title="自动化测试",
            page_icon="🤖",
            layout="wide"
        )
        
        # 自定义样式
        st.markdown("""
        <style>
        .main-container {
            background-color: #1e1e1e;
            color: #ffffff;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .title-bar {
            background-color: #2a2a2a;
            border-radius: 4px;
            padding: 16px;
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        .back-icon {
            font-size: 18px;
            margin-right: 16px;
            cursor: pointer;
        }
        .title-text {
            font-size: 20px;
            font-weight: 700;
        }
        .conversation-area {
            background-color: #2a2a2a;
            border-radius: 4px;
            padding: 16px;
            margin-bottom: 20px;
        }
        .verification-card {
            background-color: #333333;
            border-radius: 4px;
            padding: 12px;
            margin-bottom: 16px;
        }
        .verification-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .verification-title {
            font-size: 14px;
            font-weight: 500;
        }
        .verification-status {
            background-color: #721c24;
            border-radius: 4px;
            padding: 4px 12px;
            font-size: 12px;
        }
        .verification-time {
            font-size: 12px;
            color: #cccccc;
        }
        .verification-desc {
            font-size: 12px;
            color: #cccccc;
        }
        .system-message {
            background-color: #333333;
            border-radius: 4px;
            padding: 12px;
            margin-bottom: 16px;
        }
        .system-content {
            font-size: 12px;
            color: #cccccc;
        }
        .user-message {
            background-color: #3a3a3a;
            border-radius: 4px;
            padding: 12px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
        }
        .user-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background-color: #6c757d;
            margin-right: 12px;
        }
        .user-content {
            font-size: 14px;
        }
        .thinking-step {
            display: flex;
            align-items: center;
            margin-bottom: 16px;
        }
        .thinking-text {
            font-size: 12px;
            color: #6c757d;
        }
        .agent-message {
            background-color: #2d4263;
            border-radius: 4px;
            padding: 12px;
            margin-bottom: 16px;
            display: flex;
            align-items: flex-start;
        }
        .agent-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background-color: #007bff;
            margin-right: 12px;
        }
        .agent-content {
            font-size: 12px;
        }
        .evaluation-area {
            background-color: #2a2a2a;
            border-radius: 4px;
            padding: 16px;
        }
        .evaluation-header {
            font-size: 16px;
            font-weight: 500;
            margin-bottom: 12px;
        }
        .eval-item {
            display: flex;
            align-items: center;
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 12px;
        }
        .eval-item-success {
            background-color: #155724;
        }
        .eval-item-fail {
            background-color: #721c24;
        }
        .eval-icon {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 12px;
            font-size: 12px;
            font-weight: 500;
        }
        .eval-icon-success {
            background-color: #28a745;
        }
        .eval-icon-fail {
            background-color: #dc3545;
        }
        .eval-text {
            flex: 1;
            font-size: 14px;
        }
        .eval-arrow {
            font-size: 14px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 主容器
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        # 标题栏
        st.markdown('<div class="title-bar">', unsafe_allow_html=True)
        st.markdown('<div class="back-icon">&lt;</div>', unsafe_allow_html=True)
        st.markdown('<div class="title-text">模拟对话</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 对话区域
        st.markdown('<div class="conversation-area">', unsafe_allow_html=True)
        
        # 验证步骤卡片
        st.markdown('<div class="verification-card">', unsafe_allow_html=True)
        st.markdown('<div class="verification-header">', unsafe_allow_html=True)
        st.markdown('<div class="verification-title">需要身份验证</div>', unsafe_allow_html=True)
        st.markdown('<div class="verification-status">失败</div>', unsafe_allow_html=True)
        st.markdown('<div class="verification-time">1分钟前</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="verification-desc">用户的法定全名为Jane Doe，但最初提供的联系信息不正确。当要求进行身份验证时，用户提供了...</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 系统提示
        st.markdown('<div class="system-message">', unsafe_allow_html=True)
        st.markdown('<div class="system-content">• 您用于注册SalesSavvy的电子邮件地址<br>• 您的用户名或用户ID<br>• 与您账户关联的电话号码<br>• 您的账户号码（如果您在之前的通信中有）<br><br>其中任何一项都可以帮助我查找您的账户信息。</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 用户消息
        st.markdown('<div class="user-message">', unsafe_allow_html=True)
        st.markdown('<div class="user-avatar"></div>', unsafe_allow_html=True)
        st.markdown('<div class="user-content">我没有这些信息。</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 思考步骤
        st.markdown('<div class="thinking-step">', unsafe_allow_html=True)
        st.markdown('<div class="thinking-text">— Step 2 thinking →</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Agent消息
        st.markdown('<div class="agent-message">', unsafe_allow_html=True)
        st.markdown('<div class="agent-avatar"></div>', unsafe_allow_html=True)
        st.markdown('<div class="agent-content">我理解这很令人沮丧，Jane。不幸的是，如果没有账户标识符（如电子邮件、用户名、电话号码或账户号码），我无法找到并验证您的账户。</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 评测结果区域
        st.markdown('<div class="evaluation-area">', unsafe_allow_html=True)
        st.markdown('<div class="evaluation-header">评测结果</div>', unsafe_allow_html=True)
        
        # 评测项1
        st.markdown('<div class="eval-item eval-item-fail">', unsafe_allow_html=True)
        st.markdown('<div class="eval-icon eval-icon-fail">失败</div>', unsafe_allow_html=True)
        st.markdown('<div class="eval-text">流程已完成</div>', unsafe_allow_html=True)
        st.markdown('<div class="eval-arrow">&gt;</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 评测项2
        st.markdown('<div class="eval-item eval-item-success">', unsafe_allow_html=True)
        st.markdown('<div class="eval-icon eval-icon-success">成功</div>', unsafe_allow_html=True)
        st.markdown('<div class="eval-text">已回复：Fin告诉用户需要身份验证...</div>', unsafe_allow_html=True)
        st.markdown('<div class="eval-arrow">&gt;</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 评测项3
        st.markdown('<div class="eval-item eval-item-success">', unsafe_allow_html=True)
        st.markdown('<div class="eval-icon eval-icon-success">成功</div>', unsafe_allow_html=True)
        st.markdown('<div class="eval-text">已回复：Fin要求用户提供法定全名、账户...</div>', unsafe_allow_html=True)
        st.markdown('<div class="eval-arrow">&gt;</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 评测项4
        st.markdown('<div class="eval-item eval-item-fail">', unsafe_allow_html=True)
        st.markdown('<div class="eval-icon eval-icon-fail">失败</div>', unsafe_allow_html=True)
        st.markdown('<div class="eval-text">已回复：Fin要求用户提供卡的最后4位数字...</div>', unsafe_allow_html=True)
        st.markdown('<div class="eval-arrow">&gt;</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
