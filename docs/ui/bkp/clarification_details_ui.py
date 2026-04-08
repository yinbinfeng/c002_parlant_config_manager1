import streamlit as st

class ClarificationDetailsUI:
    def __init__(self):
        self.questions = [
            "流程中提到了'交易数据连接器'用于查询交易、验证详情和提交争议，但目前没有可用的数据连接器。应该使用哪些数据连接器来：(a) 通过账户ID和交易ID查询交易，(b) 检查争议资格，以及 (c) 提交争议？",
            "交易争议的具体资格标准是什么？例如：交易可以有多少天的历史仍然符合资格，客户在一段时间内可以提交的争议数量是否有上限，以及是否有其他条件会使交易不符合资格？",
            "当客户提供支持证据（例如截图）时，AI代理应该如何处理——是直接在聊天中接受文件附件，要求客户通过电子邮件发送到特定地址，还是使用其他方法？",
            "当争议不符合资格且客户希望升级到合规或风险团队时，AI代理应该如何执行此升级——是否有特定的团队、队列或流程可以移交？"
        ]
    
    def run(self):
        # 设置页面标题
        st.set_page_config(
            page_title="意图澄清",
            page_icon="❓",
            layout="centered",
            initial_sidebar_state="collapsed"
        )
        
        # 自定义样式
        st.markdown("""
        <style>
        .main-container {
            max-width: 600px;
            margin: 0 auto;
            padding: 32px;
            background-color: #1e1e1e;
            border-radius: 8px;
            color: #ffffff;
        }
        .title {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 16px;
        }
        .subtitle {
            font-size: 14px;
            color: #cccccc;
            margin-bottom: 24px;
        }
        .question {
            margin-bottom: 16px;
            font-size: 14px;
            line-height: 1.5;
        }
        .answer-input {
            margin-bottom: 24px;
        }
        .textarea {
            width: 100%;
            min-height: 80px;
            padding: 12px;
            background-color: #2a2a2a;
            border: 1px solid #444444;
            border-radius: 6px;
            color: #ffffff;
            font-family: inherit;
            font-size: 14px;
            resize: vertical;
        }
        .footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 24px;
            border-top: 1px solid #333333;
        }
        .step-indicator {
            font-size: 14px;
            color: #666666;
        }
        .generate-btn {
            background-color: #ff6b35;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 10px 24px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .generate-btn:hover {
            background-color: #ff855a;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 主容器
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        # 标题
        st.markdown('<h1 class="title">澄清详情（可选）</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">为了为您创建最佳流程，请回答以下问题：</p>', unsafe_allow_html=True)
        
        # 问题和回答输入
        answers = []
        for i, question in enumerate(self.questions):
            st.markdown(f'<div class="question">{question}</div>', unsafe_allow_html=True)
            answer = st.text_area(
                "",
                placeholder="您的回答...",
                key=f"answer_{i}",
                help=f"请回答问题 {i+1}"
            )
            answers.append(answer)
            st.markdown('<div class="answer-input"></div>', unsafe_allow_html=True)
        
        # 底部
        st.markdown('<div class="footer">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown('<div class="step-indicator">步骤 2 / 2</div>', unsafe_allow_html=True)
        with col2:
            if st.button("生成草稿", key="generate", help="生成流程草稿"):
                # 这里可以添加生成草稿的逻辑
                st.success("草稿生成中，请稍候...")
                # 模拟生成过程
                import time
                time.sleep(2)
                st.success("草稿已生成！")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    ui = ClarificationDetailsUI()
    ui.run()