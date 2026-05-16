import unittest
from datetime import UTC, date, datetime
from unittest.mock import MagicMock

from api.v1.repositories.query_jobs import increment_query_job_runs


class TestQueryJobsRepository(unittest.TestCase):
    def test_increment_query_job_runs_scopes_update_to_executor(self):
        result = MagicMock()
        result.rowcount = 1
        db = MagicMock()
        db.execute.return_value = result

        rowcount = increment_query_job_runs(
            db,
            record_id=123,
            executor_id="exec_test",
            today=date(2026, 5, 17),
            now=datetime(2026, 5, 17, tzinfo=UTC),
        )

        self.assertEqual(rowcount, 1)
        statement = str(db.execute.call_args.args[0])
        params = db.execute.call_args.args[1]

        self.assertIn("executor_id = :executor_id", statement)
        self.assertEqual(params["executor_id"], "exec_test")

