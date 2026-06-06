import json
from datetime import date

from src.analyzer import BrandAnalyzer


def test_save_plugin_batch_result_serializes_date(tmp_path):
    analyzer = BrandAnalyzer.__new__(BrandAnalyzer)
    analyzer.config = {
        "brand_analysis": {
            "plugins": {"reference_status": {"output": str(tmp_path)}}
        }
    }

    analyzer._save_plugin_batch_result(
        "reference_status",
        {"rows": [{"date": date(2026, 2, 10)}]},
        "20260210",
        "QuickCEP",
    )

    out_dir = tmp_path / "20260210"
    files = list(out_dir.glob("*.json"))
    assert len(files) == 1

    saved = json.loads(files[0].read_text(encoding="utf-8"))
    assert saved["data"]["rows"][0]["date"] == "2026-02-10"
