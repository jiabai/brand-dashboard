import json
import os
import sys
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

# 添加项目根目录到 sys.path，以便能导入 api 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _parse_component_ref(ref: str) -> Optional[Tuple[str, str]]:
    if not isinstance(ref, str) or not ref.startswith("#/components/"):
        return None
    parts = ref.lstrip("#/").split("/")
    if len(parts) != 3 or parts[0] != "components":
        return None
    return parts[1], parts[2]


def _iter_component_refs(node: Any) -> Iterable[Tuple[str, str]]:
    if isinstance(node, dict):
        ref = node.get("$ref")
        parsed = _parse_component_ref(ref) if ref is not None else None
        if parsed is not None:
            yield parsed
        for v in node.values():
            yield from _iter_component_refs(v)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_component_refs(item)


def _load_existing_info(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        info = data.get("info")
        return info if isinstance(info, dict) else None
    except Exception:
        return None


def _filter_openapi(
    full_spec: Dict[str, Any],
    *,
    include_path_prefixes: Optional[List[str]] = None,
    include_paths: Optional[List[str]] = None,
    info_override: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    full_paths = full_spec.get("paths") or {}

    filtered_paths: Dict[str, Any] = {}
    for path, item in full_paths.items():
        if include_paths is not None and path in include_paths:
            filtered_paths[path] = item
            continue
        if include_path_prefixes is not None and any(
            path.startswith(p) for p in include_path_prefixes
        ):
            filtered_paths[path] = item

    spec: Dict[str, Any] = {
        "openapi": full_spec.get("openapi"),
        "info": info_override or (full_spec.get("info") or {}),
        "paths": filtered_paths,
    }

    if "servers" in full_spec:
        spec["servers"] = full_spec["servers"]

    full_components = full_spec.get("components") or {}
    refs: Set[Tuple[str, str]] = set(_iter_component_refs(filtered_paths))

    included: Dict[str, Set[str]] = {}
    for section, name in refs:
        included.setdefault(section, set()).add(name)

    queue: List[Tuple[str, str]] = [(section, name) for section, name in refs]
    while queue:
        section, name = queue.pop()
        section_map = full_components.get(section)
        if not isinstance(section_map, dict):
            continue
        definition = section_map.get(name)
        if definition is None:
            continue
        for child_section, child_name in _iter_component_refs(definition):
            already = child_name in included.get(child_section, set())
            if not already:
                included.setdefault(child_section, set()).add(child_name)
                queue.append((child_section, child_name))

    filtered_components: Dict[str, Any] = {}
    for section, names in included.items():
        section_map = full_components.get(section)
        if not isinstance(section_map, dict):
            continue
        filtered_section: Dict[str, Any] = {}
        for name in sorted(names):
            if name in section_map:
                filtered_section[name] = section_map[name]
        if filtered_section:
            filtered_components[section] = filtered_section

    if filtered_components:
        spec["components"] = filtered_components

    return spec


def generate_openapi():
    from api.main import app

    openapi_data = app.openapi()

    api_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = os.path.join(api_dir, "docs")

    outputs = [
        ("openapi.json", openapi_data, None, None),
        ("dashboard.json", None, ["/api/v1/dashboard"], None),
        ("brand-metrics.json", None, None, ["/api/v1/dashboard/brand-metrics"]),
        (
            "platform-metrics-by-brand.json",
            None,
            None,
            ["/api/v1/dashboard/platform-metrics-by-brand"],
        ),
        ("domain-citation-rate.json", None, None, ["/api/v1/dashboard/domain-citation-rate"]),
        ("post-citation-rate.json", None, None, ["/api/v1/dashboard/post-citation-rate"]),
        ("conversation.json", None, ["/api/v1/conversation"], None),
        ("query-jobs.json", None, ["/api/v1/query-jobs"], None),
        ("executors.json", None, ["/api/v1/executors"], None),
    ]

    written_paths: List[str] = []
    for filename, direct_payload, prefixes, paths in outputs:
        output_path = os.path.join(docs_dir, filename)
        if direct_payload is not None:
            payload = direct_payload
        else:
            payload = _filter_openapi(
                openapi_data,
                include_path_prefixes=prefixes,
                include_paths=paths,
                info_override=_load_existing_info(output_path),
            )

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        written_paths.append(output_path)

    for p in written_paths:
        print(f"Wrote: {p}")

if __name__ == "__main__":
    generate_openapi()
