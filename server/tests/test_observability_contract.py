from __future__ import annotations

import ast
from pathlib import Path

from app.observability_contract import (
    CANONICAL_EVENT_NAMES,
    COUNTER_DYNAMIC_PREFIXES,
    REASON_CLASS_BY_CODE,
    REASON_CLASSES,
    classify_reason_code,
    is_canonical_counter_name,
    is_canonical_event_name,
)


MAIN_PATH = Path(__file__).resolve().parents[1] / "app" / "main.py"


def _main_module() -> ast.Module:
    return ast.parse(MAIN_PATH.read_text(encoding="utf-8"), filename=str(MAIN_PATH))


def _extract_log_event_constant_kwargs(module: ast.Module) -> tuple[set[str], set[str]]:
    events: set[str] = set()
    reasons: set[str] = set()
    for node in ast.walk(module):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "log_event":
            continue
        for kw in node.keywords:
            if kw.arg == "event" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                events.add(kw.value.value)
            if (
                kw.arg == "reason_code"
                and isinstance(kw.value, ast.Constant)
                and isinstance(kw.value.value, str)
            ):
                reasons.add(kw.value.value)
    return events, reasons


def _extract_observability_incr_args(module: ast.Module) -> tuple[set[str], set[str]]:
    static_names: set[str] = set()
    dynamic_prefixes: set[str] = set()
    for node in ast.walk(module):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "observability"
            and func.attr == "incr"
        ):
            continue
        if not node.args:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            static_names.add(arg.value)
            continue
        if isinstance(arg, ast.JoinedStr):
            prefix = "".join(
                piece.value
                for piece in arg.values
                if isinstance(piece, ast.Constant) and isinstance(piece.value, str)
            )
            dynamic_prefixes.add(prefix)
    return static_names, dynamic_prefixes


def _extract_ws_token_reason_codes(module: ast.Module) -> set[str]:
    reasons: set[str] = set()
    for node in module.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name not in {"_decode_signaling_access_token", "_validate_signaling_token_claims"}:
            continue
        for inner in ast.walk(node):
            if not isinstance(inner, ast.Raise) or inner.exc is None:
                continue
            exc = inner.exc
            if not (
                isinstance(exc, ast.Call)
                and isinstance(exc.func, ast.Name)
                and exc.func.id == "ValueError"
                and exc.args
            ):
                continue
            first = exc.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                reasons.add(first.value)
    return reasons


def test_reason_taxonomy_is_stable() -> None:
    assert REASON_CLASSES == {"operational", "security", "dependency"}
    assert REASON_CLASS_BY_CODE
    assert set(REASON_CLASS_BY_CODE.values()).issubset(REASON_CLASSES)


def test_main_log_events_use_canonical_names() -> None:
    module = _main_module()
    events, _ = _extract_log_event_constant_kwargs(module)
    assert events, "No log_event events found in main.py"
    for event in events:
        assert event in CANONICAL_EVENT_NAMES, f"event must be registered in canonical set: {event}"
        assert is_canonical_event_name(event), f"event name failed canonical validation: {event}"


def test_main_reason_codes_are_classified() -> None:
    module = _main_module()
    _, reasons = _extract_log_event_constant_kwargs(module)
    ws_token_reasons = _extract_ws_token_reason_codes(module)
    all_reasons = reasons | ws_token_reasons
    assert all_reasons, "No reason codes found in main.py"
    for reason in all_reasons:
        assert reason in REASON_CLASS_BY_CODE, f"reason_code must be classified: {reason}"
        assert classify_reason_code(reason) in REASON_CLASSES


def test_main_counter_names_follow_contract() -> None:
    module = _main_module()
    static_names, dynamic_prefixes = _extract_observability_incr_args(module)
    assert static_names, "No static observability counters found"
    for counter_name in static_names:
        assert is_canonical_counter_name(counter_name), (
            f"counter name does not match canonical contract: {counter_name}"
        )
    for prefix in dynamic_prefixes:
        assert prefix.startswith(COUNTER_DYNAMIC_PREFIXES), (
            "dynamic counter prefix must be approved: "
            f"{prefix}"
        )
