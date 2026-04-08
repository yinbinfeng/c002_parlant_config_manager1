#!/usr/bin/env python3
"""
Streamlit UI 启动脚本
文件格式: Python 源码

启动方式（推荐）：
- python egs/v0.1.0_minging_agents/run_ui.py
- 或者使用 mock 模式: python egs/v0.1.0_minging_agents/run_ui.py --mock

说明：
- 该脚本既是 Streamlit App 本体，也是"用 python 启动 Streamlit"的包装入口。
"""
import sys
import os
import argparse
from pathlib import Path
import yaml

# Add project root to Python path（保证可 import src.*）
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

DEFAULT_ENV_FILE = r"E:\cursorworkspace\c002_parlant_config_manager1\.env"
UI_MOCK_DIR = Path(__file__).parent / "config" / "mock"
UI_EXAMPLES_CONFIG_PATH = UI_MOCK_DIR / "ui_examples.yaml"

def _is_mock_mode_requested() -> bool:
    """检测是否请求了 mock 模式（支持多种传递方式）"""
    import os
    if "--mock" in sys.argv:
        return True
    if os.environ.get("PARLANT_MOCK_MODE", "").lower() in ("1", "true", "yes"):
        return True
    return False


def _rerun(st):
    fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if fn:
        fn()


def _init_state(st):
    st.session_state.setdefault("current_page", "input")
    st.session_state.setdefault("session_id", None)
    st.session_state.setdefault("poll_interval_sec", 1)
    st.session_state.setdefault("category", "示例")


def _load_system_config():
    """从 system_config.yaml 加载后台配置"""
    config_path = Path(__file__).parent / "config" / "system_config.yaml"
    try:
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"加载系统配置失败: {e}")
    return {}


def _load_ui_examples():
    """从配置文件加载UI示例数据"""
    try:
        if UI_EXAMPLES_CONFIG_PATH.exists():
            with open(UI_EXAMPLES_CONFIG_PATH, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config.get("examples", [])
    except Exception as e:
        print(f"加载UI示例配置失败: {e}")
    return []


def _load_mock_data(mock_data_file: str):
    """根据 mock 数据文件名加载对应的 mock 数据
    
    Args:
        mock_data_file: mock 数据文件名（相对于 UI_MOCK_DIR）
    """
    if not mock_data_file:
        return None
    mock_file = UI_MOCK_DIR / mock_data_file
    if mock_file.exists():
        try:
            with open(mock_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"加载mock数据失败: {e}")
    return None


class MockSessionManager:
    """Mock 版本的 SessionManager，用于 UI 测试，不调用真实 LLM"""
    
    def __init__(self, *args, **kwargs):
        self.sessions = {}
        self.example_id = None
    
    def create_session(self, *, description, data_agent_file=None, category="示例"):
        import uuid
        session_id = str(uuid.uuid4())
        
        ui_examples = _load_ui_examples()
        matched_example = None
        for ex in ui_examples:
            if ex.get("description", "").strip() == (description or "").strip():
                matched_example = ex
                break
        
        self.example_id = matched_example.get("id") if matched_example else None
        mock_data_file = matched_example.get("mock_data_file") if matched_example else None
        
        mock_data = None
        if mock_data_file:
            mock_data = _load_mock_data(mock_data_file)
        
        if mock_data:
            clarification = mock_data.get("clarification", {
                "generated_questions": [
                    {"id": "q1", "question": "目标用户群体是什么？", "answer": ""},
                    {"id": "q2", "question": "主要的业务目标是什么？", "answer": ""}
                ],
                "user_added_questions": [],
                "can_skip": True
            })
            output = mock_data.get("output", {})
        else:
            clarification = {
                "generated_questions": [
                    {"id": "q1", "question": "目标用户群体是什么？", "answer": ""},
                    {"id": "q2", "question": "主要的业务目标是什么？", "answer": ""}
                ],
                "user_added_questions": [],
                "can_skip": True
            }
            output = {}
        
        self.sessions[session_id] = {
            "session_id": session_id,
            "status": "PENDING",
            "clarification": clarification,
            "progress": {
                "overall_percent": 0,
                "current_action": "等待提交",
                "step_details": {
                    "step1": {"status": "pending", "percent": 0, "subtasks": [
                        {"name": "读取业务描述文档", "status": "pending"},
                        {"name": "分析 Data Agent 分析结果", "status": "pending"},
                        {"name": "识别关键信息缺口", "status": "pending"},
                        {"name": "生成澄清问题列表", "status": "pending"},
                        {"name": "等待用户确认", "status": "pending"}
                    ]},
                    "step2": {"status": "pending", "percent": 0, "subtasks": [
                        {"name": "多维度分析", "status": "pending"},
                        {"name": "原子化拆解", "status": "pending"}
                    ]},
                    "step3": {"status": "pending", "percent": 0, "subtasks": [
                        {"name": "流程设计 (ProcessAgent)", "status": "pending"},
                        {"name": "词汇体系设计 (GlossaryAgent)", "status": "pending"},
                        {"name": "质量检查 (QualityAgent)", "status": "pending"}
                    ]},
                    "step4": {"status": "pending", "percent": 0, "subtasks": [
                        {"name": "全局规则检查", "status": "pending"},
                        {"name": "兼容性检查", "status": "pending"}
                    ]},
                    "step5": {"status": "pending", "percent": 0, "subtasks": [
                        {"name": "目录组装", "status": "pending"},
                        {"name": "格式校验", "status": "pending"},
                        {"name": "质量检查", "status": "pending"}
                    ]},
                    "step6": {"status": "pending", "percent": 0, "subtasks": [
                        {"name": "边缘场景挖掘", "status": "pending"},
                        {"name": "补充规则生成", "status": "pending"}
                    ]},
                    "step7": {"status": "pending", "percent": 0, "subtasks": [
                        {"name": "配置组装复核", "status": "pending"}
                    ]},
                    "step8": {"status": "pending", "percent": 0, "subtasks": [
                        {"name": "最终校验与证书", "status": "pending"}
                    ]}
                },
                "estimated_remaining_sec": 30
            },
            "output": output if output else {
                "config_package_path": str(project_root / "output" / "mock_config"),
                "journeys": [],
                "guidelines": [],
                "glossary": [],
                "tools": [],
                "canned_responses": [],
                "validation": {
                    "json_files_checked": 31,
                    "json_parse_errors": 0,
                    "schema_errors": 0,
                    "journey_schema_errors": 14,
                    "state_machine_issues": 0,
                    "conflict_issues": 0,
                },
                "validation_report_path": None,
                "compliance_certificate_path": None,
            }
        }
        return session_id
    
    def submit_task(self, *, session_id):
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "ANALYZING"
            self.sessions[session_id]["progress"]["overall_percent"] = 10
            self.sessions[session_id]["progress"]["current_action"] = "正在分析您的需求..."
            self.sessions[session_id]["progress"]["step_details"]["step1"] = {
                "status": "running", 
                "percent": 20,
                "subtasks": [
                    {"name": "读取业务描述文档", "status": "completed"},
                    {"name": "分析 Data Agent 分析结果", "status": "running"},
                    {"name": "识别关键信息缺口", "status": "pending"},
                    {"name": "生成澄清问题列表", "status": "pending"},
                    {"name": "等待用户确认", "status": "pending"}
                ]
            }
            self.sessions[session_id]["progress"]["estimated_remaining_sec"] = 25
        return True
    
    def get_status(self, *, session_id):
        sess = self.sessions.get(session_id, {})
        if sess and sess.get("status") == "ANALYZING":
            sess["progress"]["overall_percent"] = min(sess["progress"]["overall_percent"] + 2, 20)
            step1 = sess["progress"]["step_details"]["step1"]
            step1["percent"] = min(step1["percent"] + 20, 100)
            subtasks = step1.get("subtasks", [])
            for i, st in enumerate(subtasks):
                if st["status"] == "running":
                    st["status"] = "completed"
                    if i + 1 < len(subtasks):
                        subtasks[i + 1]["status"] = "running"
                    break
            if step1["percent"] >= 100:
                sess["status"] = "CLARIFICATION_REQUIRED"
                sess["progress"]["current_action"] = "等待用户澄清（可跳过）"
                sess["progress"]["estimated_remaining_sec"] = 0
        elif sess and sess.get("status") == "GENERATING":
            sess["progress"]["overall_percent"] = min(sess["progress"]["overall_percent"] + 4.4, 100)
            step3 = sess["progress"]["step_details"]["step3"]
            step4 = sess["progress"]["step_details"]["step4"]
            step5 = sess["progress"]["step_details"]["step5"]
            
            if sess["progress"]["overall_percent"] <= 55:
                step3["percent"] = min(step3["percent"] + 7, 100)
                step3["status"] = "running"
                subtasks3 = step3.get("subtasks", [])
                for i, st in enumerate(subtasks3):
                    if st["status"] == "running":
                        st["status"] = "completed"
                        if i + 1 < len(subtasks3):
                            subtasks3[i + 1]["status"] = "running"
                        break
                if step3["percent"] >= 100:
                    step3["status"] = "completed"
            elif sess["progress"]["overall_percent"] <= 70:
                if step3["status"] != "completed":
                    step3["status"] = "completed"
                    step3["percent"] = 100
                step4["percent"] = min(step4["percent"] + 7, 100)
                step4["status"] = "running"
                if step4["percent"] >= 100:
                    step4["status"] = "completed"
            elif sess["progress"]["overall_percent"] <= 82:
                if step4["status"] != "completed":
                    step4["status"] = "completed"
                    step4["percent"] = 100
                step5["percent"] = min(step5["percent"] + 7, 100)
                step5["status"] = "running"
                if step5["percent"] >= 100:
                    step5["status"] = "completed"
            elif sess["progress"]["overall_percent"] <= 92:
                step6 = sess["progress"]["step_details"]["step6"]
                step6["percent"] = min(step6["percent"] + 8, 100)
                step6["status"] = "running"
                if step6["percent"] >= 100:
                    step6["status"] = "completed"
            else:
                step7 = sess["progress"]["step_details"]["step7"]
                step8 = sess["progress"]["step_details"]["step8"]
                if step7["percent"] < 100:
                    step7["percent"] = min(step7["percent"] + 12, 100)
                    step7["status"] = "running"
                    if step7["percent"] >= 100:
                        step7["status"] = "completed"
                else:
                    step8["percent"] = min(step8["percent"] + 14, 100)
                    step8["status"] = "running"
                    if step8["percent"] >= 100:
                        step8["status"] = "completed"
            
            if sess["progress"]["overall_percent"] >= 100:
                sess["status"] = "COMPLETED"
                sess["progress"]["current_action"] = "已完成"
                sess["progress"]["estimated_remaining_sec"] = 0
        return sess
    
    def get_clarification(self, *, session_id):
        return self.sessions.get(session_id, {}).get("clarification", {})
    
    def add_user_question(self, *, session_id, question, answer=""):
        import uuid
        qid = f"uq_{uuid.uuid4().hex[:8]}"
        if session_id in self.sessions:
            self.sessions[session_id]["clarification"]["user_added_questions"].append(
                {"id": qid, "question": question, "answer": answer}
            )
        return qid
    
    def update_answer(self, *, session_id, question_id, answer):
        if session_id in self.sessions:
            clar = self.sessions[session_id]["clarification"]
            for bucket in ("generated_questions", "user_added_questions"):
                for q in clar.get(bucket, []):
                    if q.get("id") == question_id:
                        q["answer"] = answer
        return True
    
    def submit_clarification(self, *, session_id):
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "GENERATING"
            self.sessions[session_id]["progress"]["overall_percent"] = 35
            self.sessions[session_id]["progress"]["current_action"] = "正在生成 Parlant 配置..."
            self.sessions[session_id]["progress"]["estimated_remaining_sec"] = 60
            self.sessions[session_id]["progress"]["step_details"]["step1"] = {"status": "completed", "percent": 100}
            self.sessions[session_id]["progress"]["step_details"]["step2"] = {"status": "completed", "percent": 100}
            self.sessions[session_id]["progress"]["step_details"]["step3"] = {
                "status": "running", 
                "percent": 30,
                "subtasks": [
                    {"name": "流程设计 (ProcessAgent)", "status": "running"},
                    {"name": "词汇体系设计 (GlossaryAgent)", "status": "pending"},
                    {"name": "质量检查 (QualityAgent)", "status": "pending"}
                ]
            }
            self.sessions[session_id]["progress"]["step_details"]["step4"] = {"status": "pending", "percent": 0}
            self.sessions[session_id]["progress"]["step_details"]["step5"] = {"status": "pending", "percent": 0}
            self.sessions[session_id]["progress"]["step_details"]["step6"] = {"status": "pending", "percent": 0}
            self.sessions[session_id]["progress"]["step_details"]["step7"] = {"status": "pending", "percent": 0}
            self.sessions[session_id]["progress"]["step_details"]["step8"] = {"status": "pending", "percent": 0}
        return True
    
    def skip_clarification(self, *, session_id):
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "GENERATING"
            self.sessions[session_id]["progress"]["overall_percent"] = 35
            self.sessions[session_id]["progress"]["current_action"] = "正在生成 Parlant 配置..."
            self.sessions[session_id]["progress"]["estimated_remaining_sec"] = 60
            self.sessions[session_id]["progress"]["step_details"]["step1"] = {"status": "completed", "percent": 100}
            self.sessions[session_id]["progress"]["step_details"]["step2"] = {"status": "completed", "percent": 100}
            self.sessions[session_id]["progress"]["step_details"]["step3"] = {
                "status": "running", 
                "percent": 30,
                "subtasks": [
                    {"name": "流程设计 (ProcessAgent)", "status": "running"},
                    {"name": "词汇体系设计 (GlossaryAgent)", "status": "pending"},
                    {"name": "质量检查 (QualityAgent)", "status": "pending"}
                ]
            }
            self.sessions[session_id]["progress"]["step_details"]["step4"] = {"status": "pending", "percent": 0}
            self.sessions[session_id]["progress"]["step_details"]["step5"] = {"status": "pending", "percent": 0}
            self.sessions[session_id]["progress"]["step_details"]["step6"] = {"status": "pending", "percent": 0}
            self.sessions[session_id]["progress"]["step_details"]["step7"] = {"status": "pending", "percent": 0}
            self.sessions[session_id]["progress"]["step_details"]["step8"] = {"status": "pending", "percent": 0}
        return True
    
    def get_result(self, *, session_id):
        return self.sessions.get(session_id, {}).get("output", {})
    
    def export_config(self, *, session_id, output_path=None):
        return str(project_root / "output" / "mock_config.zip")


def app():
    import streamlit as st
    import traceback

    st.set_page_config(page_title="会话流程规则挖掘系统", layout="wide")
    _init_state(st)
    
    st.markdown(
        """
        <style>
        :root {
          --bg: #0d0d0d;
          --panel: #1a1a1a;
          --border: #333333;
          --text: #ffffff;
          --muted: #aaaaaa;
          --accent: #ff6b35;
        }
        
        /* 全局背景和文字 */
        html, body, .stApp { 
            background: var(--bg) !important; 
            color: var(--text) !important;
        }
        
        /* 顶部Header */
        header[data-testid="stHeader"] {
            background: var(--bg) !important;
        }
        
        /* 主内容区 */
        .main .block-container {
            background: var(--bg) !important;
            color: var(--text) !important;
        }
        
        /* 所有文字颜色 */
        .main, .main * {
            color: var(--text);
        }
        
        /* 标题 */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text) !important;
        }
        
        /* 段落文字 */
        p, span, label {
            color: var(--text) !important;
        }
        
        /* 按钮样式 */
        .stButton > button {
            background: var(--panel) !important;
            color: var(--text) !important;
            border: 1px solid var(--border) !important;
            border-radius: 6px !important;
            font-weight: 500 !important;
        }
        
        .stButton > button:hover {
            background: #2a2a2a !important;
            border-color: var(--accent) !important;
        }
        
        /* 主要按钮 */
        .stButton > button[kind="primary"] {
            background: var(--accent) !important;
            color: white !important;
            border: none !important;
        }
        
        /* 文本输入框 */
        .stTextArea > div > div > textarea,
        .stTextInput > div > div > input {
            background: var(--panel) !important;
            color: var(--text) !important;
            border: 1px solid var(--border) !important;
            border-radius: 6px !important;
        }
        
        /* 文本域placeholder */
        .stTextArea > div > div > textarea::placeholder {
            color: #666666 !important;
        }
        
        /* 单选按钮 */
        .stRadio > div {
            background: transparent !important;
        }
        
        .stRadio > div > div > label {
            color: var(--text) !important;
        }
        
        /* 单选按钮选中状态 */
        .stRadio > div > div > label[data-baseweb="radio"] > div > div {
            border-color: var(--accent) !important;
        }
        
        /* 下拉选择框 */
        .stSelectbox > div > div {
            background: var(--panel) !important;
            color: var(--text) !important;
            border: 1px solid var(--border) !important;
            border-radius: 6px !important;
        }
        
        .stSelectbox > div > div > div {
            color: var(--text) !important;
        }
        
        /* 文件上传区 */
        .stFileUploader > div {
            background: var(--panel) !important;
            border: 1px solid var(--border) !important;
            border-radius: 6px !important;
        }
        
        .stFileUploader > div > div {
            background: transparent !important;
        }
        
        .stFileUploader > div > div > div,
        .stFileUploader small {
            color: var(--muted) !important;
        }
        
        /* 文件上传按钮 */
        .stFileUploader button {
            background: var(--bg) !important;
            color: var(--text) !important;
            border: 1px solid var(--border) !important;
        }
        
        /* 折叠面板 */
        .streamlit-expanderHeader {
            background: var(--panel) !important;
            color: var(--text) !important;
            border: 1px solid var(--border) !important;
            border-radius: 6px !important;
        }
        
        .streamlit-expanderContent {
            background: var(--bg) !important;
            color: var(--text) !important;
            border: 1px solid var(--border) !important;
            border-top: none !important;
        }
        
        /* 标签页 */
        .stTabs [data-baseweb="tab-list"] {
            background: var(--panel) !important;
            border-radius: 6px 6px 0 0 !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: var(--text) !important;
            background: transparent !important;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: var(--accent) !important;
            border-bottom: 2px solid var(--accent) !important;
        }
        
        /* 信息提示框 */
        .stInfo {
            background: var(--panel) !important;
            color: var(--text) !important;
            border: 1px solid var(--border) !important;
        }
        
        /* 成功提示框 */
        .stSuccess {
            background: #1e3a1e !important;
            color: #4caf50 !important;
            border: 1px solid #4caf50 !important;
        }
        
        /* 错误提示框 */
        .stError {
            background: #3a1e1e !important;
            color: #f44336 !important;
            border: 1px solid #f44336 !important;
        }
        
        /* 分隔线 */
        hr {
            border-color: var(--border) !important;
        }
        
        /* 小字说明 */
        .stCaption {
            color: var(--muted) !important;
        }
        
        /* 侧边栏 */
        .css-1d391kg, .css-1lcbmhc {
            background: var(--panel) !important;
        }
        
        /* 隐藏顶部装饰线 */
        .stApp > header {
            background: var(--bg) !important;
        }
        
        /* 进度条 */
        .stProgress > div > div {
            background: var(--panel) !important;
        }
        
        .stProgress > div > div > div {
            background: var(--accent) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    if _is_mock_mode_requested():
        st.info("🚀 运行在 MOCK 模式 - UI 测试专用，不调用真实 LLM")
        if "mock_mgr" not in st.session_state:
            st.session_state.mock_mgr = MockSessionManager()
        mgr = st.session_state.mock_mgr
    else:
        try:
            from src.mining_agents.managers.session_manager import SessionManager
        except Exception as e:
            st.error(f"导入 SessionManager 失败: {e}")
            st.code(traceback.format_exc())
            return
        
        if "real_mgr" not in st.session_state:
            system_config = _load_system_config()
            max_parallel = system_config.get("max_parallel_agents", 1)
            st.session_state.real_mgr = SessionManager(
                system_config_path=str(project_root / "egs" / "v0.1.0_minging_agents" / "config" / "system_config.yaml"),
                base_work_dir=str(project_root / "output"),
                env_file=DEFAULT_ENV_FILE if os.path.exists(DEFAULT_ENV_FILE) else None,
                mode="real",
                max_parallel=max_parallel,
            )
        mgr = st.session_state.real_mgr

    # --------------------
    # 页面 1：主入口（需求输入）
    # --------------------
    if st.session_state.current_page == "input":
        st.markdown("## 让AI为您起草流程")
        st.write("描述一个流程，AI将从您的工作区中提取上下文来创建初稿。生成后您可以完善草稿。")

        # 加载示例数据
        ui_examples = _load_ui_examples()
        
        # 示例选项区域
        if ui_examples:
            st.markdown("### 快速开始 - 选择示例")
            example_cols = st.columns(min(len(ui_examples), 5))
            for idx, example in enumerate(ui_examples[:5]):
                with example_cols[idx]:
                    if st.button(
                        example.get("title", f"示例{idx+1}"),
                        key=f"example_btn_{example.get('id', idx)}",
                        use_container_width=True
                    ):
                        st.session_state.selected_example = example
                        st.session_state.business_desc = example.get("description", "")
                        st.session_state.category = example.get("category", "示例")
                        _rerun(st)
            st.divider()

        desc = st.text_area("需求描述", key="business_desc", height=180, placeholder="粘贴您现有的SOP/流程描述…")
        data_file = st.file_uploader("文件上传（可选，仅 JSON）", type=["json"])

        st.write("分类标签（用于示例/记录）")
        st.session_state.category = st.radio(
            "category",
            options=["示例", "软件服务", "电商", "金融科技", "游戏"],
            horizontal=True,
            label_visibility="collapsed",
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            start_disabled = len((desc or "").strip()) == 0
            if st.button("继 续", disabled=start_disabled, type="primary"):
                tmp_path = None
                if data_file is not None:
                    # 先落盘到 output/tmp，SessionManager 会在 create_session 内复制到 session/store
                    tmp_dir = project_root / "output" / "tmp_uploads"
                    tmp_dir.mkdir(parents=True, exist_ok=True)
                    tmp_path = tmp_dir / data_file.name
                    tmp_path.write_bytes(data_file.getvalue())

                sid = mgr.create_session(
                    description=desc,
                    data_agent_file=str(tmp_path) if tmp_path else None,
                    category=st.session_state.category,
                )
                st.session_state.session_id = sid
                mgr.submit_task(session_id=sid)
                st.session_state.current_page = "wait_step1"
                _rerun(st)

        with col2:
            if st.session_state.session_id:
                st.caption(f"当前 session_id: `{st.session_state.session_id}`")

        st.caption("步骤 1 / 8")
        return

    # session must exist
    sid = st.session_state.session_id
    if not sid:
        st.session_state.current_page = "input"
        _rerun(st)
        return

    status = mgr.get_status(session_id=sid)
    st.caption(f"session_id: `{sid}`  |  status: `{status.get('status')}`")

    # --------------------
    # 页面 2：Step1 等待（轮询状态）
    # --------------------
    if st.session_state.current_page == "wait_step1":
        st.markdown("## 正在分析您的需求…")
        
        progress = status.get("progress", {})
        prog = progress.get("overall_percent", 0)
        current_action = progress.get("current_action", "处理中")
        estimated_sec = progress.get("estimated_remaining_sec", 0)
        
        loading_placeholder = st.empty()
        with loading_placeholder.container():
            st.markdown(
                """
                <div style="text-align: center; padding: 20px;">
                    <div style="font-size: 48px; animation: spin 1s linear infinite; display: inline-block;">⟳</div>
                    <style>
                        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
                    </style>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown(f"<p style='text-align: center; font-size: 18px;'>{current_action}</p>", unsafe_allow_html=True)
        
        st.markdown("### 处理进度")
        st.progress(int(prog) / 100.0)
        st.write(f"**{prog}%**")
        
        st.markdown("### 当前状态")
        step_details = progress.get("step_details", {})
        step1 = step_details.get("step1", {})
        subtasks = step1.get("subtasks", [])
        
        if subtasks:
            status_container = st.container()
            with status_container:
                for task in subtasks:
                    task_status = task.get("status", "pending")
                    task_name = task.get("name", "未知任务")
                    if task_status == "completed":
                        icon = "✓"
                        color = "#4caf50"
                    elif task_status == "running":
                        icon = "⟳"
                        color = "#2196f3"
                    else:
                        icon = "○"
                        color = "#666666"
                    st.markdown(f"<span style='color: {color};'>{icon} {task_name}</span>", unsafe_allow_html=True)
        
        if estimated_sec > 0:
            st.markdown(f"**预计剩余时间: 约 {estimated_sec} 秒**")
        
        if status.get("status") == "CLARIFICATION_REQUIRED":
            st.success("处理完成，准备进入澄清环节...")
            st.session_state.current_page = "clarification"
            _rerun(st)
            return
        if status.get("status") == "FAILED":
            st.session_state.current_page = "failed"
            _rerun(st)
            return

        import time
        time.sleep(int(st.session_state.poll_interval_sec))
        _rerun(st)
        st.caption("步骤 1 / 5")
        return

    # --------------------
    # 页面 3：澄清（可跳过）
    # --------------------
    if st.session_state.current_page == "clarification":
        clarification_container = st.container()
        with clarification_container:
            st.markdown("## 澄清详情（可选）")
            st.write("为了为您创建最佳流程，请回答以下问题。您也可以跳过此步骤。")

            clar = mgr.get_clarification(session_id=sid)
            gen_qs = clar.get("generated_questions") or []
            user_qs = clar.get("user_added_questions") or []

            st.subheader("系统问题")
            for q in gen_qs:
                qid = q.get("id")
                st.write(f"**{qid}**：{q.get('question')}")
                ans = st.text_area(f"{qid} 的回答", value=q.get("answer", ""), key=f"ans_{qid}", height=80)
                mgr.update_answer(session_id=sid, question_id=qid, answer=ans)
                st.divider()

            st.subheader("补充问题（可选）")
            for q in user_qs:
                qid = q.get("id")
                with st.expander(f"{qid}: {q.get('question')}", expanded=False):
                    ans = st.text_area("回答", value=q.get("answer", ""), key=f"uans_{qid}", height=80)
                    mgr.update_answer(session_id=sid, question_id=qid, answer=ans)

            with st.expander("+ 添加问题", expanded=False):
                uq = st.text_input("您的问题", key="new_q")
                ua = st.text_area("您的回答（可选）", key="new_a", height=80)
                if st.button("保存问题"):
                    if not (uq or "").strip():
                        st.error("问题内容不能为空")
                    else:
                        mgr.add_user_question(session_id=sid, question=uq.strip(), answer=(ua or "").strip())
                        st.session_state["new_q"] = ""
                        st.session_state["new_a"] = ""
                        _rerun(st)

            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("跳 过"):
                    mgr.skip_clarification(session_id=sid)
                    st.session_state.current_page = "wait_generate"
                    st.session_state.clarification_done = True
                    _rerun(st)
            with c2:
                if st.button("生 成 草 稿", type="primary"):
                    mgr.submit_clarification(session_id=sid)
                    st.session_state.current_page = "wait_generate"
                    st.session_state.clarification_done = True
                    _rerun(st)

            st.caption("步骤 2 / 8")
        return

    # --------------------
    # 页面 4：Step3-8 等待
    # --------------------
    if st.session_state.current_page == "wait_generate":
        st.markdown("## 正在生成 Parlant 配置…")
        
        progress = status.get("progress", {})
        prog = progress.get("overall_percent", 0)
        current_action = progress.get("current_action", "处理中")
        estimated_sec = progress.get("estimated_remaining_sec", 0)
        
        loading_placeholder = st.empty()
        with loading_placeholder.container():
            st.markdown(
                """
                <div style="text-align: center; padding: 20px;">
                    <div style="font-size: 48px; animation: spin 1s linear infinite; display: inline-block;">⟳</div>
                    <style>
                        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
                    </style>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown(f"<p style='text-align: center; font-size: 18px;'>{current_action}</p>", unsafe_allow_html=True)
        
        st.markdown("### 整体进度")
        st.progress(int(prog) / 100.0)
        st.write(f"**{prog}%**")
        
        step_details = progress.get("step_details", {})
        
        def render_step_progress(step_key, step_title, step_num):
            step_data = step_details.get(step_key, {})
            step_status = step_data.get("status", "pending")
            step_percent = step_data.get("percent", 0)
            subtasks = step_data.get("subtasks", [])
            
            if step_status == "completed":
                status_icon = "✓"
                status_text = "已完成"
                header_color = "#4caf50"
            elif step_status == "running":
                status_icon = "⟳"
                status_text = "进行中"
                header_color = "#2196f3"
            else:
                status_icon = "○"
                status_text = "待开始"
                header_color = "#666666"
            
            with st.expander(f"Step {step_num}: {step_title} {status_icon} {status_text}", expanded=(step_status == "running")):
                st.progress(int(step_percent) / 100.0)
                st.write(f"**{step_percent}%**")
                if subtasks:
                    st.markdown("**子任务:**")
                    for task in subtasks:
                        task_status = task.get("status", "pending")
                        task_name = task.get("name", "未知任务")
                        if task_status == "completed":
                            icon = "✓"
                        elif task_status == "running":
                            icon = "⟳"
                        else:
                            icon = "○"
                        st.write(f"{icon} {task_name}")
        
        render_step_progress("step3", "工作流并行开发", 3)
        render_step_progress("step4", "全局规则检查与优化", 4)
        render_step_progress("step5", "分支SOP并发挖掘", 5)
        render_step_progress("step6", "边缘场景挖掘", 6)
        render_step_progress("step7", "配置组装", 7)
        render_step_progress("step8", "最终校验与输出", 8)
        
        if estimated_sec > 0:
            st.markdown(f"**预计剩余时间: 约 {estimated_sec} 秒**")
        
        if status.get("status") == "COMPLETED":
            st.success("配置生成完成！")
            st.session_state.current_page = "result"
            _rerun(st)
            return
        if status.get("status") == "FAILED":
            st.session_state.current_page = "failed"
            _rerun(st)
            return

        import time
        time.sleep(int(st.session_state.poll_interval_sec))
        _rerun(st)
        st.caption("步骤 3-8 / 8")
        return

    # --------------------
    # 页面 5：结果展示
    # --------------------
    if st.session_state.current_page == "result":
        st.markdown("## Parlant 配置生成完成")
        out = mgr.get_result(session_id=sid)
        cfg_path = out.get("config_package_path")
        
        col_export, col_regenerate = st.columns([1, 1])
        with col_export:
            if st.button("导出配置（ZIP）", type="primary"):
                zip_path = mgr.export_config(session_id=sid)
                st.success(f"已导出：`{zip_path}`")
        with col_regenerate:
            if st.button("重新生成"):
                st.session_state.current_page = "input"
                st.session_state.session_id = None
                _rerun(st)
        
        validation = out.get("validation") or {}
        if validation:
            st.markdown("### Step8 校验摘要")
            c1, c2, c3 = st.columns(3)
            c1.metric("JSON文件校验数", validation.get("json_files_checked", 0))
            c2.metric("Journey Schema Errors", validation.get("journey_schema_errors", 0))
            c3.metric("State/Conflict Issues", (validation.get("state_machine_issues", 0) + validation.get("conflict_issues", 0)))
            st.caption(f"parse_errors={validation.get('json_parse_errors', 0)} | schema_errors={validation.get('schema_errors', 0)}")

            report_path = out.get("validation_report_path")
            cert_path = out.get("compliance_certificate_path")
            if report_path or cert_path:
                st.caption(
                    f"report: `{report_path}`\n\ncert: `{cert_path}`"
                    if report_path or cert_path
                    else ""
                )

            with st.expander("Step8 校验详情（Top 错误样例）", expanded=False):
                # 1) 优先读取真实 report
                if report_path:
                    try:
                        from pathlib import Path
                        p = Path(str(report_path))
                        if p.exists():
                            txt = p.read_text(encoding="utf-8", errors="ignore")
                            lines = txt.splitlines()
                            # 仅展示前 200 行，避免 UI 卡顿
                            st.code("\n".join(lines[:200]))
                        else:
                            st.info("校验报告文件不存在，可能尚未生成。")
                    except Exception as e:
                        st.warning(f"读取校验报告失败: {type(e).__name__}: {e}")
                else:
                    # 2) mock / 无文件场景：展示摘要提示
                    st.info("当前无校验报告文件路径（可能是 mock 会话）。请以摘要指标为准。")

        st.divider()
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["流程", "规则", "术语", "工具", "固定话术"])
        
        with tab1:
            st.subheader("流程视图")
            journeys = out.get("journeys", [])
            guidelines = out.get("guidelines", [])
            tools = out.get("tools", [])
            canned_responses = out.get("canned_responses", [])
            
            if journeys:
                guideline_map = {g.get("id"): g for g in guidelines}
                tool_map = {t.get("name"): t for t in tools}
                cr_map = {cr.get("id"): cr for cr in canned_responses}
                
                main_journeys = [j for j in journeys if j.get("sop_type") == "main" or not j.get("sop_type")]
                branch_journeys = [j for j in journeys if j.get("sop_type") == "branch"]
                edge_journeys = [j for j in journeys if j.get("sop_type") == "edge"]
                
                journey_map = {j.get("id"): j for j in journeys}
                
                def render_journey_tree(journey_list, indent=0):
                    for j in journey_list:
                        jid = j.get("id")
                        jname = j.get("name", f"流程{jid}")
                        sop_type = j.get("sop_type", "main")
                        parent_id = j.get("parent_sop_id")
                        
                        type_label = {"main": "主流程", "branch": "分支流程", "edge": "边缘场景"}.get(sop_type, "主流程")
                        type_color = {"main": "#4caf50", "branch": "#2196f3", "edge": "#ff9800"}.get(sop_type, "#4caf50")
                        
                        prefix = "  " * indent + ("└─ " if indent > 0 else "")
                        
                        col_name, col_type, col_parent = st.columns([3, 1, 2])
                        with col_name:
                            st.markdown(f"{prefix}**{jname}**")
                        with col_type:
                            st.markdown(f"<span style='color: {type_color}; font-size: 12px;'>[{type_label}]</span>", unsafe_allow_html=True)
                        with col_parent:
                            if parent_id and parent_id in journey_map:
                                parent_name = journey_map[parent_id].get("name", parent_id)
                                parent_state = j.get("parent_state_id", "")
                                st.caption(f"← {parent_name}" + (f" ({parent_state})" if parent_state else ""))
                
                st.markdown("**流程层级结构**")
                st.markdown("---")
                
                if main_journeys:
                    st.markdown("#### 主流程")
                    render_journey_tree(main_journeys)
                    
                    for mj in main_journeys:
                        mj_id = mj.get("id")
                        child_branches = [j for j in branch_journeys if j.get("parent_sop_id") == mj_id]
                        child_edges = [j for j in edge_journeys if j.get("parent_sop_id") == mj_id]
                        
                        if child_branches:
                            st.markdown(f"**├─ 分支流程**")
                            render_journey_tree(child_branches, indent=1)
                        if child_edges:
                            st.markdown(f"**├─ 边缘场景**")
                            render_journey_tree(child_edges, indent=1)
                
                st.markdown("---")
                
                journey_names = [j.get("name", f"流程{i+1}") for i, j in enumerate(journeys)]
                selected_idx = st.selectbox(
                    "选择流程查看详情",
                    range(len(journeys)),
                    format_func=lambda i: journey_names[i],
                    key="journey_select"
                )
                selected_journey = journeys[selected_idx]
                
                col_list, col_graph = st.columns([1, 2])
                with col_list:
                    st.markdown("**流程信息**")
                    sop_type = selected_journey.get("sop_type", "main")
                    type_label = {"main": "主流程", "branch": "分支流程", "edge": "边缘场景"}.get(sop_type, "主流程")
                    st.markdown(f"**类型:** {type_label}")
                    
                    parent_id = selected_journey.get("parent_sop_id")
                    if parent_id and parent_id in journey_map:
                        parent_name = journey_map[parent_id].get("name", parent_id)
                        parent_state = selected_journey.get("parent_state_id", "")
                        st.markdown(f"**父流程:** {parent_name}" + (f" (节点: {parent_state})" if parent_state else ""))
                    
                    st.markdown(f"**描述:** {selected_journey.get('description', 'N/A')}")
                    
                    st.markdown("**节点关联资源**")
                    nodes = selected_journey.get("nodes", [])
                    for node in nodes:
                        node_label = node.get("label", node.get("id"))
                        bind_guidelines = node.get("bind_guideline_ids", [])
                        bind_tool = node.get("bind_tool_id")
                        bind_crs = node.get("bind_canned_response_ids", [])
                        
                        has_binding = bind_guidelines or bind_tool or bind_crs
                        if has_binding:
                            with st.expander(f"📍 {node_label}", expanded=False):
                                if bind_guidelines:
                                    st.markdown("**关联规则:**")
                                    for gid in bind_guidelines:
                                        g = guideline_map.get(gid)
                                        if g:
                                            st.markdown(f"  • {g.get('name', gid)} (`{gid}`)")
                                        else:
                                            st.markdown(f"  • `{gid}` (未找到)")
                                if bind_tool:
                                    st.markdown(f"**关联工具:** `{bind_tool}`")
                                    t = tool_map.get(bind_tool)
                                    if t:
                                        st.caption(f"  {t.get('description', '')[:50]}...")
                                if bind_crs:
                                    st.markdown("**关联话术:**")
                                    for crid in bind_crs:
                                        cr = cr_map.get(crid)
                                        if cr:
                                            content_preview = cr.get('content', '')[:30]
                                            st.markdown(f"  • `{crid}`: {content_preview}...")
                
                with col_graph:
                    st.markdown("**流程图**")
                    nodes = selected_journey.get("nodes", [])
                    edges = selected_journey.get("edges", [])
                    
                    node_map = {n.get("id"): n for n in nodes}
                    
                    if nodes:
                        for i, node in enumerate(nodes):
                            node_type = node.get("type", "action")
                            label = node.get("label", "节点")
                            
                            bind_guidelines = node.get("bind_guideline_ids", [])
                            bind_tool = node.get("bind_tool_id")
                            bind_crs = node.get("bind_canned_response_ids", [])
                            has_binding = bind_guidelines or bind_tool or bind_crs
                            
                            if node_type == "start":
                                color = "#4caf50"
                            elif node_type == "end":
                                color = "#f44336"
                            else:
                                color = "#2196f3" if not has_binding else "#9c27b0"
                            
                            node_cols = st.columns([1, 2, 1])
                            border_radius = "50%" if node_type in ["start", "end"] else "8px"
                            binding_indicator = " 🔗" if has_binding else ""
                            
                            with node_cols[1]:
                                st.markdown(
                                    f"<div style='background: {color}; color: white; padding: 12px 24px; "
                                    f"border-radius: {border_radius}; "
                                    f"text-align: center; font-weight: 500; box-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{label}{binding_indicator}</div>",
                                    unsafe_allow_html=True
                                )
                            
                            if i < len(nodes) - 1:
                                line_cols = st.columns([1, 2, 1])
                                with line_cols[1]:
                                    st.markdown(
                                        "<div style='display: flex; flex-direction: column; align-items: center; height: 50px;'>"
                                        "<div style='width: 2px; height: 20px; background: #666;'></div>"
                                        "<div style='color: #666; font-size: 14px; margin: -5px 0;'>▼</div>"
                                        "<div style='width: 2px; height: 20px; background: #666;'></div>"
                                        "</div>",
                                        unsafe_allow_html=True
                                    )
                        
                        st.caption("🔗 紫色节点表示有关联的规则/工具/话术")
                    
                    if edges:
                        with st.expander("查看连接详情", expanded=False):
                            for edge in edges:
                                from_node = node_map.get(edge.get("from"), {}).get("label", edge.get("from"))
                                to_node = node_map.get(edge.get("to"), {}).get("label", edge.get("to"))
                                st.write(f"{from_node} → {to_node}")
            else:
                st.info("暂无流程数据")
        
        with tab2:
            st.subheader("规则视图")
            guidelines = out.get("guidelines", [])
            journeys = out.get("journeys", [])
            canned_responses = out.get("canned_responses", [])
            
            if guidelines:
                cr_map = {cr.get("id"): cr for cr in canned_responses}
                journey_node_map = {}
                for j in journeys:
                    for node in j.get("nodes", []):
                        for gid in node.get("bind_guideline_ids", []):
                            if gid not in journey_node_map:
                                journey_node_map[gid] = []
                            journey_node_map[gid].append({
                                "journey_name": j.get("name"),
                                "node_label": node.get("label"),
                                "sop_type": j.get("sop_type", "main")
                            })
                
                scope_filter = st.selectbox(
                    "按作用域筛选",
                    ["全部", "agent_global", "sop_only"],
                    key="guideline_scope_filter"
                )
                
                filtered_guidelines = guidelines
                if scope_filter != "全部":
                    filtered_guidelines = [g for g in guidelines if g.get("scope") == scope_filter]
                
                for g in filtered_guidelines:
                    gid = g.get("id")
                    with st.expander(f"**{g.get('name', '未命名规则')}** (ID: {g.get('id', 'N/A')})", expanded=False):
                        col_info, col_relations = st.columns([2, 1])
                        
                        with col_info:
                            st.markdown(f"**触发条件:** {g.get('trigger', 'N/A')}")
                            st.markdown(f"**执行动作:** {g.get('action', 'N/A')}")
                            st.markdown(f"**优先级:** {g.get('priority', 'N/A')} | **组合模式:** {g.get('composition', 'N/A')}")
                            st.markdown(f"**作用域:** {g.get('scope', 'N/A')}")
                        
                        with col_relations:
                            related_crs = [cr for cr in canned_responses if cr.get("related_rule") == gid]
                            if related_crs:
                                st.markdown("**关联话术:**")
                                for cr in related_crs:
                                    content_preview = cr.get('content', '')[:30]
                                    st.markdown(f"  • `{cr.get('id')}`: {content_preview}...")
                            
                            used_in = journey_node_map.get(gid, [])
                            if used_in:
                                st.markdown("**使用位置:**")
                                for loc in used_in:
                                    type_icon = {"main": "🟢", "branch": "🔵", "edge": "🟠"}.get(loc["sop_type"], "⚪")
                                    st.markdown(f"  {type_icon} {loc['journey_name']} → {loc['node_label']}")
            else:
                st.info("暂无规则数据")
        
        with tab3:
            st.subheader("术语视图")
            glossary = out.get("glossary", [])
            if glossary:
                for term in glossary:
                    with st.expander(f"**{term.get('term', '未命名术语')}**", expanded=False):
                        st.markdown(f"**定义:** {term.get('definition', 'N/A')}")
                        st.markdown(f"**使用场景:** {term.get('usage', 'N/A')}")
                        synonyms = term.get('synonyms', [])
                        if synonyms:
                            st.markdown(f"**同义词:** {', '.join(synonyms)}")
            else:
                st.info("暂无术语数据")
        
        with tab4:
            st.subheader("工具视图")
            tools = out.get("tools", [])
            journeys = out.get("journeys", [])
            
            if tools:
                tool_usage_map = {}
                for j in journeys:
                    for node in j.get("nodes", []):
                        tool_id = node.get("bind_tool_id")
                        if tool_id:
                            if tool_id not in tool_usage_map:
                                tool_usage_map[tool_id] = []
                            tool_usage_map[tool_id].append({
                                "journey_name": j.get("name"),
                                "node_label": node.get("label"),
                                "sop_type": j.get("sop_type", "main")
                            })
                
                for tool in tools:
                    tool_name = tool.get("name")
                    with st.expander(f"**{tool_name}**", expanded=False):
                        col_info, col_relations = st.columns([2, 1])
                        
                        with col_info:
                            st.markdown(f"**描述:** {tool.get('description', 'N/A')}")
                            
                            input_params = tool.get('input_params', [])
                            if input_params:
                                st.markdown("**输入参数:**")
                                for p in input_params:
                                    required = "必填" if p.get('required') else "可选"
                                    st.write(f"• {p.get('name')} ({p.get('type')}, {required}) - {p.get('description', '')}")
                            
                            output_params = tool.get('output_params', [])
                            if output_params:
                                st.markdown("**输出参数:**")
                                for p in output_params:
                                    st.write(f"• {p.get('name')} ({p.get('type')}) - {p.get('description', '')}")
                            
                            st.markdown(f"**使用场景:** {tool.get('usage', 'N/A')}")
                        
                        with col_relations:
                            used_in = tool_usage_map.get(tool_name, [])
                            if used_in:
                                st.markdown("**使用位置:**")
                                for loc in used_in:
                                    type_icon = {"main": "🟢", "branch": "🔵", "edge": "🟠"}.get(loc["sop_type"], "⚪")
                                    st.markdown(f"  {type_icon} {loc['journey_name']} → {loc['node_label']}")
                            else:
                                st.markdown("**使用位置:** 暂无")
            else:
                st.info("暂无工具数据")
        
        with tab5:
            st.subheader("固定话术视图")
            canned_responses = out.get("canned_responses", [])
            guidelines = out.get("guidelines", [])
            journeys = out.get("journeys", [])
            
            if canned_responses:
                guideline_map = {g.get("id"): g for g in guidelines}
                
                cr_usage_map = {}
                for j in journeys:
                    for node in j.get("nodes", []):
                        for crid in node.get("bind_canned_response_ids", []):
                            if crid not in cr_usage_map:
                                cr_usage_map[crid] = []
                            cr_usage_map[crid].append({
                                "journey_name": j.get("name"),
                                "node_label": node.get("label"),
                                "sop_type": j.get("sop_type", "main")
                            })
                
                for cr in canned_responses:
                    crid = cr.get("id")
                    related_rule_id = cr.get("related_rule")
                    with st.expander(f"**{crid}**", expanded=False):
                        col_info, col_relations = st.columns([2, 1])
                        
                        with col_info:
                            st.markdown(f"**话术内容:**")
                            st.markdown(f"> {cr.get('content', 'N/A')}")
                            st.markdown(f"**使用场景:** {cr.get('usage', 'N/A')}")
                            variables = cr.get('variables', [])
                            if variables:
                                st.markdown(f"**变量占位符:** {', '.join(['{' + v + '}' for v in variables])}")
                        
                        with col_relations:
                            if related_rule_id:
                                related_rule = guideline_map.get(related_rule_id)
                                if related_rule:
                                    st.markdown(f"**关联规则:**")
                                    st.markdown(f"  • {related_rule.get('name', related_rule_id)}")
                                    st.caption(f"  触发: {related_rule.get('trigger', '')[:40]}...")
                                else:
                                    st.markdown(f"**关联规则:** `{related_rule_id}`")
                            
                            used_in = cr_usage_map.get(crid, [])
                            if used_in:
                                st.markdown("**使用位置:**")
                                for loc in used_in:
                                    type_icon = {"main": "🟢", "branch": "🔵", "edge": "🟠"}.get(loc["sop_type"], "⚪")
                                    st.markdown(f"  {type_icon} {loc['journey_name']} → {loc['node_label']}")
            else:
                st.info("暂无固定话术数据")
        
        st.caption("步骤 8 / 8 完成")
        return

    # --------------------
    # 失败页
    # --------------------
    if st.session_state.current_page == "failed":
        st.markdown("## 生成失败")
        err = (status.get("last_error") or {})
        st.error(err.get("message") or "未知错误")
        tb = err.get("traceback")
        if tb:
            st.code(tb)
        if st.button("返 回 首 页"):
            st.session_state.current_page = "input"
            st.session_state.session_id = None
            _rerun(st)


def _load_dotenv_safe():
    """安全地加载 dotenv，如果模块不存在则跳过"""
    try:
        from dotenv import load_dotenv
        if os.path.exists(DEFAULT_ENV_FILE):
            load_dotenv(DEFAULT_ENV_FILE)
            print(f"已加载环境变量文件：{DEFAULT_ENV_FILE}")
    except ImportError:
        print("警告: python-dotenv 模块未安装，跳过加载 .env 文件")


def _launch_streamlit(mock_mode=False):
    """启动 Streamlit 服务器"""
    _load_dotenv_safe()
    
    # 使用 Streamlit CLI 启动应用
    import streamlit.web.cli as stcli
    
    # 保存原始 argv
    original_argv = sys.argv.copy()
    
    # 设置 streamlit 启动参数
    # -- 之后的参数会传递给脚本而不是 Streamlit
    args = [
        "streamlit",
        "run",
        __file__,
        "--server.fileWatcherType=none"
    ]
    if mock_mode:
        args.append("--")
        args.append("--mock")
    
    sys.argv = args
    
    try:
        stcli.main()
    except SystemExit:
        pass
    finally:
        # 恢复原始 argv
        sys.argv = original_argv


def _is_running_under_streamlit():
    """检测当前是否在 Streamlit 运行环境下"""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        return get_script_run_ctx() is not None
    except Exception:
        return False


def main():
    """主入口函数 - 简单直接的启动方式"""
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="启动会话流程规则挖掘系统 UI")
    parser.add_argument("--mock", action="store_true", help="启用 mock 模式（用于 UI 测试）")
    args = parser.parse_args()
    
    # 设置环境变量以持久化 mock 模式（Streamlit 重载后仍有效）
    if args.mock:
        os.environ["PARLANT_MOCK_MODE"] = "1"
    
    _load_dotenv_safe()
    
    # 直接使用 streamlit 库启动
    try:
        import streamlit.web.cli as stcli
    except ImportError:
        print("错误: 未找到 streamlit，请先安装依赖: pip install -r requirements.txt")
        sys.exit(1)
    
    # 保存原始 argv
    original_argv = sys.argv.copy()
    
    # 构建 streamlit 命令
    sys.argv = [
        "streamlit",
        "run",
        __file__,
        "--server.fileWatcherType=none"
    ]
    if args.mock:
        sys.argv.append("--")
        sys.argv.append("--mock")
    
    print(f"启动 Streamlit 应用 (mock模式: {args.mock})...")
    try:
        stcli.main()
    except SystemExit:
        pass
    finally:
        # 恢复原始 argv
        sys.argv = original_argv


if __name__ == "__main__":
    if _is_running_under_streamlit():
        app()
    else:
        main()
else:
    if "--mock" in sys.argv:
        os.environ["PARLANT_MOCK_MODE"] = "1"
        sys.argv = [arg for arg in sys.argv if arg != "--mock"]
    app()