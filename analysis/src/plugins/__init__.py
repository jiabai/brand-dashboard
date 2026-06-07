"""插件聚合入口。

提供扁平化导入路径，并保持插件模块可通过 `src.plugins.<plugin_name>` 访问。
"""

import sys

from .metrics import mention_status as _metrics_mention_status
from .metrics import reference_status as _metrics_reference_status

mention_status = _metrics_mention_status
reference_status = _metrics_reference_status

sys.modules[__name__ + ".mention_status"] = _metrics_mention_status
sys.modules[__name__ + ".reference_status"] = _metrics_reference_status

__all__ = ["mention_status", "reference_status"]

try:
    from .utils import extract_source as _utils_extract_source

    extract_source = _utils_extract_source
    sys.modules[__name__ + ".extract_source"] = _utils_extract_source
    __all__.append("extract_source")
except ImportError:
    pass

try:
    from .utils import import_mention_data as _utils_import_mention_data

    import_mention_data = _utils_import_mention_data
    sys.modules[__name__ + ".import_mention_data"] = _utils_import_mention_data
    __all__.append("import_mention_data")
except ImportError:
    pass

try:
    from .utils import llm_ping as _utils_llm_ping

    llm_ping = _utils_llm_ping
    sys.modules[__name__ + ".llm_ping"] = _utils_llm_ping
    __all__.append("llm_ping")
except ImportError:
    pass
