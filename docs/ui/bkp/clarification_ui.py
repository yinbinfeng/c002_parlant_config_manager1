import streamlit as st

class ClarificationUI:
    def __init__(self):
        self.examples = [
            "取消或暂停订阅 — 更改前确认计划详情和下次 billing 日期",
            "解决失败或待处理的付款 — 验证付款状态，重试或指导客户更新方法",
            "更新 delivery 地址 — 检查 shipment 是否已发货，如符合条件则更新"
        ]
        self.categories = ["示例", "软件服务", "电商", "金融科技", "游戏"]
    
    def run(self):
        # 设置页面标题
        st.set_page_config(
            page_title="AI流程起草",
            page_icon="🤖",
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
            margin-bottom: 24px;
        }
        .input-area {
            margin-bottom: 24px;
        }
        .textarea {
            width: 100%;
            min-height: 160px;
            padding: 16px;
            background-color: #2a2a2a;
            border: 1px solid #444444;
            border-radius: 8px;
            color: #ffffff;
            font-family: inherit;
            font-size: 14px;
            resize: vertical;
        }
        .category-tags {
            display: flex;
            gap: 8px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }
        .tag {
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .tag.active {
            background-color: #ff6b35;
            color: #ffffff;
        }
        .tag.inactive {
            background-color: #333333;
            color: #ffffff;
        }
        .examples-list {
            margin-bottom: 32px;
        }
        .example-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #333333;
            font-size: 14px;
        }
        .example-item:last-child {
            border-bottom: none;
        }
        .copy-btn {
            background-color: #333333;
            color: #666666;
            border: none;
            border-radius: 4px;
            padding: 4px 8px;
            cursor: pointer;
            font-size: 12px;
        }
        .copy-btn:hover {
            background-color: #444444;
            color: #ffffff;
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
        .continue-btn {
            background-color: #333333;
            color: #ffffff;
            border: 1px solid #444444;
            border-radius: 6px;
            padding: 10px 24px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .continue-btn:hover {
            background-color: #444444;
        }
        .continue-btn:disabled {
            background-color: #222222;
            color: #666666;
            cursor: not-allowed;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 主容器
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        # 标题
        st.markdown('<h1 class="title">让AI为您起草流程</h1>', unsafe_allow_html=True)
        
        # 输入区域
        st.markdown('<div class="input-area">', unsafe_allow_html=True)
        user_input = st.text_area(
            "",
            placeholder="描述一个流程，AI将从您的工作区中提取上下文来创建初稿。粘贴您现有的SOP。生成后您可以完善草稿。",
            key="user_input",
            help="请详细描述您的流程需求"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 分类标签
        st.markdown('<div class="category-tags">', unsafe_allow_html=True)
        selected_category = st.radio(
            "",
            self.categories,
            horizontal=True,
            key="category",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 示例列表
        st.markdown('<div class="examples-list">', unsafe_allow_html=True)
        for i, example in enumerate(self.examples):
            col1, col2 = st.columns([9, 1])
            with col1:
                st.markdown(f'<div class="example-item">{example}</div>', unsafe_allow_html=True)
            with col2:
                if st.button("↑", key=f"copy_{i}", help="复制到输入框"):
                    st.session_state.user_input = example
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 底部
        st.markdown('<div class="footer">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown('<div class="step-indicator">步骤 1 / 2</div>', unsafe_allow_html=True)
        with col2:
            continue_disabled = len(user_input.strip()) == 0
            # 继续按钮由run_ui.py控制
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    ui = ClarificationUI()
    ui.run()