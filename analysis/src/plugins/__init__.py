"""插件聚合入口。

提供扁平化导入路径，并保持插件模块可通过 `src.plugins.<plugin_name>` 访问。
"""

import sys

from .metrics import mention_status as _metrics_mention_status
from .metrics import reference_status as _metrics_reference_status
from .utils import extract_source as _utils_extract_source
from .utils import import_mention_data as _utils_import_mention_data
from .utils import llm_ping as _utils_llm_ping

mention_status = _metrics_mention_status
reference_status = _metrics_reference_status
extract_source = _utils_extract_source
import_mention_data = _utils_import_mention_data
llm_ping = _utils_llm_ping

sys.modules[__name__ + ".mention_status"] = _metrics_mention_status
sys.modules[__name__ + ".reference_status"] = _metrics_reference_status
sys.modules[__name__ + ".extract_source"] = _utils_extract_source
sys.modules[__name__ + ".import_mention_data"] = _utils_import_mention_data
sys.modules[__name__ + ".llm_ping"] = _utils_llm_ping

__all__ = [
    "mention_status",
    "reference_status",
    "extract_source",
    "import_mention_data",
    "llm_ping",
]
