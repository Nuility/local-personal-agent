"""Offline integration tests: fake model responses, real queue and memory database."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import agent


class Integration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original = agent.DATA
        agent.DATA = Path(self.temp.name)

    def tearDown(self):
        agent.DATA = self.original
        self.temp.cleanup()

    def test_empty_init_and_deleted_memory_stays_deleted(self):
        agent.init(); agent.init()
        with agent.db() as con:
            self.assertEqual(con.execute("SELECT count(*) FROM memory").fetchone()[0], 0)
        mid = agent.remember("profile", "测试偏好", "test", "confirmed")
        agent.change_memory(mid, "delete")
        agent.init()
        self.assertEqual(agent.recall("测试偏好"), [])

    def test_candidate_and_correction(self):
        old = agent.remember("profile", "偏好旧方案", "user", "confirmed")
        pending = agent.remember("profile", "未经确认的猜测", "agent")
        self.assertNotIn(pending, [r["id"] for r in agent.recall("猜测")])
        with self.assertRaises(ValueError):
            agent.remember("profile", "候选替代", "agent", replaces=old)
        new = agent.remember("profile", "偏好新方案", "user", "confirmed", old)
        recalled = [r["id"] for r in agent.recall("方案")]
        self.assertIn(new, recalled); self.assertNotIn(old, recalled)
        reverted = agent.remember("profile", "偏好旧方案", "user", "confirmed", new)
        self.assertEqual(reverted, old)
        self.assertNotIn(new, [r["id"] for r in agent.recall("方案")])
        agent.change_memory(new, "delete")
        self.assertNotIn(new, [r["id"] for r in agent.recall("方案")])

    def test_independent_workflow_feeds_main_memory(self):
        jid = agent.submit("planning", "私人知识库项目的实施计划")
        with patch.object(agent, "generate", side_effect=["需求分析", "计划草稿", "最终计划", json.dumps({"summary": "私人知识库项目分三阶段实施，尚未执行。"}, ensure_ascii=False)]):
            self.assertTrue(agent.run_one())
        with agent.db() as con:
            job = con.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
            self.assertEqual(job["state"], "done"); self.assertEqual(job["step"], 3)
        self.assertIn(jid, agent.context("私人知识库"))
        self.assertIn("尚未执行", agent.context("私人知识库"))

    def test_failed_step_resumes_from_checkpoint(self):
        jid = agent.submit("research", "测试材料")
        with patch.object(agent, "generate", side_effect=["完成第一步", RuntimeError("model offline")]):
            agent.run_one()
        with agent.db() as con:
            row = con.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
            self.assertEqual(row["state"], "failed"); self.assertEqual(row["step"], 1)
            con.execute("UPDATE jobs SET state='queued' WHERE id=?", (jid,))
        with patch.object(agent, "generate", side_effect=["第二步", "第三步", '{"summary":"测试材料分析产出"}']) as call:
            agent.run_one()
            self.assertEqual(call.call_count, 3)
        self.assertFalse(agent.run_one())

    def test_core_applies_to_every_model_call(self):
        with patch.object(agent, "api", return_value={"message": {"content": "ok"}}) as call:
            agent.generate("专业工作流职责", "测试任务")
            payload = call.call_args.args[1]
            system = payload["messages"][0]["content"]
            core = agent.settings_file("core_principles.md").read_text(encoding="utf-8")
            self.assertTrue(system.startswith(core))
            self.assertIn("专业工作流职责", system)


if __name__ == "__main__":
    unittest.main()
