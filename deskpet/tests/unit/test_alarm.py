"""마감 알람(SQLite) 오프라인 단위 테스트. 하드웨어·인터넷·스피커 없이 실행된다.

실행:  python -m unittest discover -s tests/unit -v
"""
import importlib
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

SRC = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(SRC))


class AlarmTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["DESKPET_HOME"] = self.tmp.name
        import deskpet_alarm
        self.alarm = importlib.reload(deskpet_alarm)  # DESKPET_HOME을 새로 읽게 한다
        self.played = []
        patcher = mock.patch.object(self.alarm, "notify", side_effect=lambda t, v="": self.played.append(t))
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def rows(self):
        con = self.alarm.db_connect()
        try:
            return [dict(r) for r in con.execute("SELECT * FROM reminders")]
        finally:
            con.close()

    def test_db_is_created_in_deskpet_home(self):
        self.alarm.db_connect().close()
        self.assertTrue((Path(self.tmp.name) / "reminders.sqlite3").is_file())

    def test_alert_is_one_hour_before_deadline(self):
        self.alarm.add_reminder("보고서", "+3h", cache_voice=False)
        row = self.rows()[0]
        self.assertEqual(row["deadline_ts"] - row["alert_ts"], 3600)
        self.assertEqual(row["state"], "pending")

    def test_not_alerted_before_time(self):
        self.alarm.add_reminder("보고서", "+3h", cache_voice=False)
        self.alarm.check_due()
        self.assertEqual(self.played, [])
        self.assertEqual(self.rows()[0]["state"], "pending")

    def test_alerted_once_inside_last_hour(self):
        self.alarm.add_reminder("발표 준비", "+30m", cache_voice=False)
        self.alarm.check_due()
        self.alarm.check_due()
        self.assertEqual(self.played, ["발표 준비"])  # 반복하지 않음
        self.assertEqual(self.rows()[0]["state"], "alerted")

    def test_expired_after_deadline(self):
        self.alarm.add_reminder("지난 일", "+2m", cache_voice=False)
        with mock.patch.object(self.alarm.time, "time", return_value=time.time() + 600):
            self.alarm.check_due()
        self.assertEqual(self.played, [])
        self.assertEqual(self.rows()[0]["state"], "expired")

    def test_failed_playback_is_retried(self):
        self.alarm.add_reminder("재시도", "+30m", cache_voice=False)
        with mock.patch.object(self.alarm, "notify", side_effect=OSError("aplay 없음")):
            self.alarm.check_due()
        self.assertEqual(self.rows()[0]["state"], "pending")
        self.alarm.check_due()
        self.assertEqual(self.rows()[0]["state"], "alerted")

    def test_duplicate_add_returns_same_id(self):
        first = self.alarm.add_reminder("같은 일", "2099-01-01 10:00", cache_voice=False)
        second = self.alarm.add_reminder("같은 일", "2099-01-01 10:00", cache_voice=False)
        self.assertEqual(first, second)
        self.assertEqual(len(self.rows()), 1)

    def test_parse_deadline_rejects_bad_input(self):
        for bad in ("2099-01-01", "2000-01-01 10:00", "내일"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.alarm.parse_deadline(bad)

    def test_parse_deadline_formats(self):
        local = self.alarm.parse_deadline("2099-01-01 10:00")
        self.assertEqual(local.utcoffset().total_seconds(), 9 * 3600)
        utc = self.alarm.parse_deadline("2099-01-01T01:00:00Z")
        self.assertEqual(local, utc)
        epoch_ms = self.alarm.parse_deadline(int(local.timestamp() * 1000))
        self.assertEqual(local, epoch_ms)

    def test_register_from_backend_with_nested_deadline(self):
        response = {
            "type": "task_created",
            "data": {"task": {"id": 7, "title": "회의록", "deadline": "2099-01-01T10:00:00+09:00"}},
        }
        with mock.patch.object(self.alarm, "tts_cache", return_value=""):
            self.assertTrue(self.alarm.register_from_backend(response))
        row = self.rows()[0]
        self.assertEqual(row["title"], "회의록")
        self.assertEqual(row["source_key"], "backend:7")

    def test_register_from_backend_without_deadline_is_skipped(self):
        response = {"type": "task_created", "output": {"tts": "내일 3시까지 보고서 등록했어요"}}
        self.assertFalse(self.alarm.register_from_backend(response))
        self.assertEqual(self.rows(), [])

    def test_register_ignores_other_types(self):
        self.assertFalse(self.alarm.register_from_backend({"type": "chat", "deadline": "2099-01-01 10:00"}))


if __name__ == "__main__":
    unittest.main()
