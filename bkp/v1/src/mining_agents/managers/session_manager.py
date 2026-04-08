#!/usr/bin/env python3
"""
session_manager.py
文件格式: Python 源码

为 UI/CLI 提供统一的“会话 + 状态机 + 断点续跑”能力。

- 状态持久化：session.json（文件存储，便于调试与恢复）
- 任务执行：后台线程 + asyncio.run() 执行 step pipeline
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import json
import shutil
import threading
import traceback
import uuid
import zipfile

from dotenv import load_dotenv

from ..utils.logger import logger
from ..utils.file_utils import ensure_dir, read_json, write_json
from ..engine import build_core_engine


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_industry(business_desc: str) -> str:
    """从业务描述中提取行业关键词"""
    if not business_desc:
        return "通用"
    
    industry_keywords = {
        "保险": "保险",
        "金融": "金融",
        "银行": "银行",
        "电商": "电商",
        "零售": "零售",
        "医疗": "医疗",
        "教育": "教育",
        "旅游": "旅游",
        "物流": "物流",
        "制造": "制造",
        "保险": "保险",
        "证券": "证券",
        "基金": "基金",
    }
    
    for keyword, industry in industry_keywords.items():
        if keyword in business_desc:
            return industry
    
    return "通用"


@dataclass(frozen=True)
class SessionPaths:
    root: Path
    store_dir: Path
    session_file: Path
    config_file: Path
    output_dir: Path
    export_dir: Path


class SessionManager:
    """
    SessionManager（文件存储版）

    说明：
    - 设计文档中描述了 API 路由；这里以 Python 方法形式提供同样的语义，
      便于在 Streamlit UI 中直接调用。
    """

    def __init__(
        self,
        *,
        system_config_path: str,
        base_work_dir: str,
        env_file: Optional[str] = None,
        mode: str = "real",
        max_parallel: int = 1,
    ) -> None:
        self.system_config_path = str(system_config_path)
        self.base_work_dir = Path(base_work_dir).resolve()
        self.mode = mode
        self.max_parallel = max_parallel

        if env_file:
            try:
                if Path(env_file).exists():
                    load_dotenv(env_file)
                    logger.info(f"已加载环境变量文件：{env_file}")
                else:
                    logger.warning(f"环境变量文件不存在，将仅使用系统环境变量：{env_file}")
            except Exception as e:
                logger.error(f"加载环境变量文件失败：{type(e).__name__}: {e}")

        ensure_dir(str(self.base_work_dir))
        self._locks: dict[str, threading.Lock] = {}

    def _paths(self, session_id: str) -> SessionPaths:
        root = self.base_work_dir / "sessions" / session_id
        store_dir = root / "store"
        output_dir = root / "output"
        export_dir = root / "exports"
        return SessionPaths(
            root=root,
            store_dir=store_dir,
            session_file=store_dir / "session.json",
            config_file=store_dir / "system_config.yaml",
            output_dir=output_dir,
            export_dir=export_dir,
        )

    def _lock(self, session_id: str) -> threading.Lock:
        if session_id not in self._locks:
            self._locks[session_id] = threading.Lock()
        return self._locks[session_id]

    def _read_session(self, session_id: str) -> dict[str, Any]:
        p = self._paths(session_id).session_file
        if not p.exists():
            raise FileNotFoundError(f"session_id 不存在：{session_id}")
        return read_json(str(p))

    def _write_session(self, session_id: str, data: dict[str, Any]) -> None:
        paths = self._paths(session_id)
        ensure_dir(str(paths.store_dir))
        write_json(data, str(paths.session_file))

    def create_session(
        self,
        *,
        description: str,
        data_agent_file: Optional[str] = None,
        category: str = "示例",
    ) -> str:
        session_id = str(uuid.uuid4())
        paths = self._paths(session_id)
        ensure_dir(str(paths.store_dir))
        ensure_dir(str(paths.output_dir))
        ensure_dir(str(paths.export_dir))

        # 复制 system_config，并将 output_base_dir 指向本 session 的 output 目录
        try:
            src_cfg = Path(self.system_config_path)
            cfg_text = src_cfg.read_text(encoding="utf-8")
            # 简单替换 output_base_dir（保持 YAML 其余内容不变）
            # 注意：以 session 目录为锚点，避免多 session 写到同一 output
            # 这里写绝对路径，避免相对路径基准不一致。
            output_dir_str = str(paths.output_dir).replace("\\", "/")
            out_line = f'output_base_dir: "{output_dir_str}"'
            lines = []
            replaced = False
            for line in cfg_text.splitlines():
                if line.strip().startswith("output_base_dir:"):
                    lines.append(out_line)
                    replaced = True
                else:
                    lines.append(line)
            if not replaced:
                lines.append(out_line)
            paths.config_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        except Exception as e:
            logger.error(f"创建 session 配置失败：{type(e).__name__}: {e}")
            raise

        stored_data_agent_file = None
        if data_agent_file:
            try:
                src = Path(data_agent_file)
                if src.exists():
                    dst = paths.store_dir / src.name
                    shutil.copy2(src, dst)
                    stored_data_agent_file = str(dst)
            except Exception as e:
                logger.warning(f"复制 data_agent_file 失败，将忽略：{type(e).__name__}: {e}")

        payload = {
            "session_id": session_id,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "input": {
                "description": description,
                "data_agent_file": stored_data_agent_file,
                "category": category,
            },
            "status": "PENDING",
            "current_step": 0,
            "clarification": {
                "generated_questions": [],
                "user_added_questions": [],
                "can_skip": True,
            },
            "progress": {
                "overall_percent": 0,
                "current_action": "等待提交",
                "step_details": {
                    "step1": {"status": "pending", "percent": 0},
                    "step2": {"status": "pending", "percent": 0},
                    "step3": {"status": "pending", "percent": 0},
                    "step4": {"status": "pending", "percent": 0},
                    "step5": {"status": "pending", "percent": 0},
                },
            },
            "output": {
                "config_package_path": None,
                "intermediate_files": [],
            },
            "last_error": None,
        }
        self._write_session(session_id, payload)
        return session_id

    def submit_task(self, *, session_id: str) -> bool:
        with self._lock(session_id):
            sess = self._read_session(session_id)
            if sess.get("status") not in {"PENDING", "FAILED", "IDLE"}:
                return True

            sess["status"] = "ANALYZING"
            sess["current_step"] = 1
            sess["updated_at"] = _now_iso()
            sess["progress"]["current_action"] = "Step1：生成澄清问题"
            sess["progress"]["overall_percent"] = 5
            sess["progress"]["step_details"]["step1"] = {"status": "running", "percent": 10}
            self._write_session(session_id, sess)

            t = threading.Thread(target=self._run_step1_background, args=(session_id,), daemon=True)
            t.start()
            return True

    def get_status(self, *, session_id: str) -> dict[str, Any]:
        with self._lock(session_id):
            return self._read_session(session_id)

    def get_clarification(self, *, session_id: str) -> dict[str, Any]:
        with self._lock(session_id):
            sess = self._read_session(session_id)
            return sess.get("clarification", {}) or {}

    def add_user_question(self, *, session_id: str, question: str, answer: str = "") -> str:
        qid = f"uq_{uuid.uuid4().hex[:8]}"
        with self._lock(session_id):
            sess = self._read_session(session_id)
            sess.setdefault("clarification", {}).setdefault("user_added_questions", []).append(
                {"id": qid, "question": question, "answer": answer}
            )
            sess["updated_at"] = _now_iso()
            self._write_session(session_id, sess)
        return qid

    def update_answer(self, *, session_id: str, question_id: str, answer: str) -> bool:
        with self._lock(session_id):
            sess = self._read_session(session_id)
            clar = sess.setdefault("clarification", {})
            updated = False
            for bucket in ("generated_questions", "user_added_questions"):
                for q in clar.get(bucket, []) or []:
                    if q.get("id") == question_id:
                        q["answer"] = answer
                        updated = True
            if updated:
                sess["updated_at"] = _now_iso()
                self._write_session(session_id, sess)
            return updated

    def submit_clarification(self, *, session_id: str) -> bool:
        with self._lock(session_id):
            sess = self._read_session(session_id)
            if sess.get("status") not in {"CLARIFICATION_REQUIRED"}:
                return False
            sess["status"] = "CLARIFICATION_ANSWERED"
            sess["updated_at"] = _now_iso()
            sess["progress"]["current_action"] = "澄清已提交，开始生成配置"
            sess["progress"]["overall_percent"] = 25
            self._write_session(session_id, sess)

            t = threading.Thread(target=self._run_steps2to5_background, args=(session_id, True), daemon=True)
            t.start()
            return True

    def skip_clarification(self, *, session_id: str) -> bool:
        with self._lock(session_id):
            sess = self._read_session(session_id)
            if sess.get("status") not in {"CLARIFICATION_REQUIRED"}:
                return False
            sess["status"] = "CLARIFICATION_SKIPPED"
            sess["updated_at"] = _now_iso()
            sess["progress"]["current_action"] = "已跳过澄清，开始生成配置"
            sess["progress"]["overall_percent"] = 25
            self._write_session(session_id, sess)

            t = threading.Thread(target=self._run_steps2to5_background, args=(session_id, False), daemon=True)
            t.start()
            return True

    def get_result(self, *, session_id: str) -> dict[str, Any]:
        with self._lock(session_id):
            sess = self._read_session(session_id)
            return sess.get("output", {}) or {}

    def export_config(self, *, session_id: str, output_path: Optional[str] = None) -> str:
        with self._lock(session_id):
            sess = self._read_session(session_id)
            cfg_path = (sess.get("output") or {}).get("config_package_path")
            if not cfg_path:
                raise ValueError("当前 session 尚未生成配置包")

            paths = self._paths(session_id)
            ensure_dir(str(paths.export_dir))

            zip_target = Path(output_path) if output_path else (paths.export_dir / "parlant_config.zip")
            zip_target.parent.mkdir(parents=True, exist_ok=True)

            root = Path(cfg_path)
            if not root.exists():
                raise FileNotFoundError(f"配置包目录不存在：{root}")

            with zipfile.ZipFile(str(zip_target), "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for p in root.rglob("*"):
                    if p.is_file():
                        arc = str(p.relative_to(root)).replace("\\", "/")
                        zf.write(str(p), arcname=arc)

            return str(zip_target)

    # -------------------------
    # Background runners
    # -------------------------

    def _run_step1_background(self, session_id: str) -> None:
        try:
            paths = self._paths(session_id)
            sess = self._read_session(session_id)
            business_desc = (sess.get("input") or {}).get("description", "")

            step_manager, orchestrator = build_core_engine(
                config_path=str(paths.config_file),
                output_dir=str(paths.output_dir),
                mode=self.mode,
                max_parallel=self.max_parallel,
                debug_mode=False,
            )

            import asyncio

            async def _run():
                ctx = {
                    "business_desc": business_desc,
                    "core_goal": business_desc[:200] if business_desc else "",
                    "industry": _extract_industry(business_desc),
                    "mock_mode": self.mode == "mock",
                    "debug_mode": False,
                    "force_rerun": False,
                    "ui_mode": True,
                    "step1_output_dir": str(step_manager.get_step_output_dir(1)),
                }
                return await step_manager.run_step(1, ctx)

            result = asyncio.run(_run())

            # 从 step1_questions.json 优先读取结构化问题
            step1_dir = step_manager.get_step_output_dir(1)
            questions_json = step1_dir / "step1_questions.json"
            questions = []
            if questions_json.exists():
                try:
                    questions = json.loads(questions_json.read_text(encoding="utf-8")).get("questions", []) or []
                except Exception:
                    questions = (result or {}).get("clarification_questions", []) or []
            else:
                questions = (result or {}).get("clarification_questions", []) or []

            with self._lock(session_id):
                sess = self._read_session(session_id)
                sess["status"] = "CLARIFICATION_REQUIRED"
                sess["current_step"] = 2
                sess["updated_at"] = _now_iso()
                sess["progress"]["current_action"] = "等待用户澄清（可跳过）"
                sess["progress"]["overall_percent"] = 20
                sess["progress"]["step_details"]["step1"] = {"status": "completed", "percent": 100}
                sess["clarification"]["generated_questions"] = [
                    {"id": q.get("id"), "question": q.get("question"), "answer": q.get("answer", "")}
                    for q in (questions or [])
                    if isinstance(q, dict)
                ]
                self._write_session(session_id, sess)

            asyncio.run(orchestrator.cleanup())
        except Exception as e:
            with self._lock(session_id):
                sess = self._read_session(session_id)
                sess["status"] = "FAILED"
                sess["updated_at"] = _now_iso()
                sess["last_error"] = {
                    "message": f"{type(e).__name__}: {e}",
                    "traceback": traceback.format_exc(),
                }
                sess["progress"]["current_action"] = "Step1 失败"
                self._write_session(session_id, sess)

    def _run_steps2to5_background(self, session_id: str, use_clarification: bool) -> None:
        try:
            paths = self._paths(session_id)
            sess = self._read_session(session_id)
            business_desc = (sess.get("input") or {}).get("description", "")

            # 汇总澄清回答（generated + user_added）
            clar = sess.get("clarification", {}) or {}
            questions = []
            for q in (clar.get("generated_questions") or []):
                if isinstance(q, dict):
                    questions.append(q)
            for q in (clar.get("user_added_questions") or []):
                if isinstance(q, dict):
                    questions.append(q)

            step_manager, orchestrator = build_core_engine(
                config_path=str(paths.config_file),
                output_dir=str(paths.output_dir),
                mode=self.mode,
                max_parallel=self.max_parallel,
                debug_mode=False,
            )

            import asyncio

            async def _run():
                ctx = {
                    "business_desc": business_desc,
                    "core_goal": business_desc[:200] if business_desc else "",
                    "industry": _extract_industry(business_desc),
                    "mock_mode": self.mode == "mock",
                    "debug_mode": False,
                    "force_rerun": False,
                    "step1_output_dir": str(step_manager.get_step_output_dir(1)),
                    "clarification_questions": questions if use_clarification else [],
                    "use_clarification": use_clarification,
                }
                # Step2 会从 step1_output_dir 回填 structured_requirements 等
                await step_manager.run_steps(start_step=2, end_step=5, context=ctx)
                return ctx

            with self._lock(session_id):
                sess = self._read_session(session_id)
                sess["status"] = "GENERATING"
                sess["current_step"] = 3
                sess["updated_at"] = _now_iso()
                sess["progress"]["current_action"] = "Step2-5：生成配置中"
                sess["progress"]["overall_percent"] = 35
                self._write_session(session_id, sess)

            asyncio.run(_run())

            # Step5 产物路径
            step5_dir = step_manager.get_step_output_dir(5)
            step5_result = step5_dir / "result.json"
            parlant_root = None
            if step5_result.exists():
                try:
                    data = json.loads(step5_result.read_text(encoding="utf-8"))
                    parlant_root = data.get("parlant_config_package")
                except Exception:
                    parlant_root = None

            with self._lock(session_id):
                sess = self._read_session(session_id)
                sess["status"] = "COMPLETED"
                sess["current_step"] = 5
                sess["updated_at"] = _now_iso()
                sess["progress"]["current_action"] = "已完成"
                sess["progress"]["overall_percent"] = 100
                for k in ("step2", "step3", "step4", "step5"):
                    sess["progress"]["step_details"][k] = {"status": "completed", "percent": 100}
                sess.setdefault("output", {})["config_package_path"] = parlant_root
                self._write_session(session_id, sess)

            asyncio.run(orchestrator.cleanup())
        except Exception as e:
            with self._lock(session_id):
                sess = self._read_session(session_id)
                sess["status"] = "FAILED"
                sess["updated_at"] = _now_iso()
                sess["last_error"] = {
                    "message": f"{type(e).__name__}: {e}",
                    "traceback": traceback.format_exc(),
                }
                sess["progress"]["current_action"] = "生成失败"
                self._write_session(session_id, sess)

