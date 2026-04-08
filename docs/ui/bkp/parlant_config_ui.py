import streamlit as st

class ParlantConfigUI:
    def __init__(self):
        pass
    
    def run(self):
        st.set_page_config(
            page_title="Parlant 配置管理",
            page_icon="📋",
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
        }
        .tab-container {
            background-color: #2a2a2a;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .flow-diagram {
            background-color: #2a2a2a;
            border-radius: 6px;
            padding: 24px;
            margin: 16px 0;
        }
        .flow-node {
            background-color: #333333;
            border-radius: 4px;
            padding: 12px;
            margin-bottom: 16px;
        }
        .flow-node-final {
            background-color: #4caf50;
            border-radius: 4px;
            padding: 12px;
            margin-bottom: 16px;
        }
        .flow-line {
            text-align: center;
            margin: 8px 0;
            color: #cccccc;
        }
        .card {
            background-color: #333333;
            border-radius: 6px;
            padding: 16px;
            margin: 12px 0;
        }
        .card-title {
            font-weight: 600;
            margin-bottom: 8px;
            color: #ffffff;
        }
        .card-content {
            color: #cccccc;
            font-size: 14px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 主容器
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        # 标题
        st.title("Parlant 配置管理")
        
        # 标签卡
        tab1, tab2, tab3, tab4 = st.tabs(["流程", "规则", "术语", "工具"])
        
        # 流程标签卡
        with tab1:
            st.markdown('<div class="tab-container">', unsafe_allow_html=True)
            st.header("预约挂号全流程")
            st.markdown('<div class="flow-diagram">', unsafe_allow_html=True)
            
            # 流程节点1
            st.markdown('<div class="flow-node">', unsafe_allow_html=True)
            st.subheader("1. 科室选择")
            st.write("用户进入预约系统后，首先选择就诊科室")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 连接线1
            st.markdown('<div class="flow-line">↓</div>', unsafe_allow_html=True)
            
            # 流程节点2
            st.markdown('<div class="flow-node">', unsafe_allow_html=True)
            st.subheader("2. 加载医生")
            st.write("系统根据选择的科室加载可预约的医生列表")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 连接线2
            st.markdown('<div class="flow-line">↓</div>', unsafe_allow_html=True)
            
            # 流程节点3
            st.markdown('<div class="flow-node">', unsafe_allow_html=True)
            st.subheader("3. 选择时段")
            st.write("用户从医生列表中选择具体的医生和可预约时段")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 连接线3
            st.markdown('<div class="flow-line">↓</div>', unsafe_allow_html=True)
            
            # 流程节点4
            st.markdown('<div class="flow-node">', unsafe_allow_html=True)
            st.subheader("4. 信息确认")
            st.write("用户确认预约信息，包括科室、医生、时段等")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 连接线4
            st.markdown('<div class="flow-line">↓</div>', unsafe_allow_html=True)
            
            # 流程节点5
            st.markdown('<div class="flow-node">', unsafe_allow_html=True)
            st.subheader("5. 提交预约")
            st.write("用户提交预约请求，系统处理预约信息")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 连接线5
            st.markdown('<div class="flow-line">↓</div>', unsafe_allow_html=True)
            
            # 流程节点6
            st.markdown('<div class="flow-node-final">', unsafe_allow_html=True)
            st.subheader("6. 预约完成")
            st.write("预约成功，系统生成预约凭证和相关信息")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 规则标签卡
        with tab2:
            st.markdown('<div class="tab-container">', unsafe_allow_html=True)
            st.header("医疗相关规则")
            
            # 规则1
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("医疗问候规则")
            st.write("使用温和、专业的语言向患者问好，表达关心和专业态度")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 规则2
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("医疗安抚规则")
            st.write("当患者表达焦虑或担忧时，提供适当的安抚和支持")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 规则3
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("医疗无诊断规则")
            st.write("避免对患者进行诊断，仅提供一般性健康建议")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 规则4
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("医疗转人工规则")
            st.write("当遇到复杂医疗问题时，建议患者咨询专业医生")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 术语标签卡
        with tab3:
            st.markdown('<div class="tab-container">', unsafe_allow_html=True)
            st.header("医疗相关术语")
            
            # 术语1
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("专家号")
            st.write("由副主任医师及以上级别的医生提供的挂号服务，通常需要提前预约")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 术语2
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("普通号")
            st.write("由主治医师及以下级别的医生提供的挂号服务，通常更容易预约")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 术语3
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("化验结果")
            st.write("通过实验室检测获得的患者身体状况相关数据，用于辅助诊断")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 工具标签卡
        with tab4:
            st.markdown('<div class="tab-container">', unsafe_allow_html=True)
            st.header("医疗相关工具")
            
            # 工具1
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("医院科室查询")
            st.write("查询医院各科室的详细信息，包括科室介绍、医生信息等")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 工具2
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("医生排班查询")
            st.write("查询医生的出诊时间安排，便于患者选择合适的就诊时间")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 工具3
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("预约挂号")
            st.write("在线预约医院挂号服务，避免现场排队等候")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    ui = ParlantConfigUI()
    ui.run()