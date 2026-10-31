from __future__ import annotations

import uuid
from typing import Any, Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from meridian.graph.nodes import (
    apply_hitl_decision,
    draft_node,
    plan_node,
    retrieve_node,
    self_heal_node,
)
from meridian.graph.state import DeskState
from meridian.observability import span
from meridian.store import store


def _hitl_node(state: DeskState) -> dict[str, Any]:
    if not state.get("hitl_required"):
        return {"status": "ok"}
    proposed = state.get("proposed") or {}
    ticker = proposed.get("ticker") or (state.get("tickers") or [""])[0]
    current = store.get(ticker)
    payload = {
        "title": _hitl_title(state.get("intent", ""), ticker),
        "detail": "Mutates shared desk coverage. Requires PM/analyst approval.",
        "intent": state.get("intent"),
        "current": current.model_dump() if current else None,
        "proposed": proposed,
    }
    decision = interrupt(payload)
    if isinstance(decision, dict):
        return {"hitl_decision": decision, **apply_hitl_decision({**state, "hitl_decision": decision})}
    return {"hitl_decision": {"action": decision}}


def _hitl_title(intent: str, ticker: str) -> str:
    if intent == "watchlist_add":
        return f"Add {ticker} to watchlist"
    if intent == "watchlist_remove":
        return f"Remove {ticker} from watchlist"
    return f"File desk note — {ticker}"


def _route_after_heal(state: DeskState) -> Literal["hitl", "done"]:
    return "hitl" if state.get("hitl_required") else "done"


def build_graph() -> Any:
    graph = StateGraph(DeskState)
    graph.add_node("plan", plan_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("draft", draft_node)
    graph.add_node("self_heal", self_heal_node)
    graph.add_node("hitl", _hitl_node)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "retrieve")
    graph.add_edge("retrieve", "draft")
    graph.add_edge("draft", "self_heal")
    graph.add_conditional_edges("self_heal", _route_after_heal, {"hitl": "hitl", "done": END})
    graph.add_edge("hitl", END)
    return graph.compile(checkpointer=MemorySaver())


compiled_graph = build_graph()


def _thread_config(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}}


def _interrupt_payload(thread_id: str) -> dict[str, Any] | None:
    snapshot = compiled_graph.get_state(_thread_config(thread_id))
    if not snapshot.next:
        return None
    for task in snapshot.tasks:
        interrupts = getattr(task, "interrupts", None) or ()
        for item in interrupts:
            value = getattr(item, "value", item)
            if isinstance(value, dict):
                return value
    return {"title": "Paused for desk approval"}


def _pack(state: dict[str, Any], thread_id: str, paused: bool) -> dict[str, Any]:
    steps = [
        {"name": "plan", "detail": state.get("intent", ""), "ms": 0},
        {
            "name": "retrieve",
            "detail": f"{len(state.get('documents') or [])} docs via "
            + (", ".join(state.get("tools_used") or []) or "none"),
            "ms": 0,
        },
        {
            "name": "draft",
            "detail": "HITL " + state.get("intent", "") if paused else f"{len(state.get('citations') or [])} citations",
            "ms": 0,
        },
    ]
    if state.get("healed"):
        steps.append({"name": "self_check", "detail": "healed", "ms": 0})
    elif not paused:
        steps.append(
            {
                "name": "self_check",
                "detail": "grounded" if state.get("grounded") else "ungrounded",
                "ms": 0,
            }
        )
    status = "paused" if paused else state.get("status") or "ok"
    if status == "running":
        status = "ok"
    return {
        "thread_id": thread_id,
        "status": status,
        "intent": state.get("intent", "research"),
        "tickers": state.get("tickers") or [],
        "question": state.get("question", ""),
        "briefing": state.get("draft", ""),
        "citations": state.get("citations") or [],
        "provider": state.get("provider", "fixture"),
        "grounded": bool(state.get("grounded")),
        "healed": bool(state.get("healed")),
        "tools_used": state.get("tools_used") or [],
        "steps": steps,
        "hitl": _interrupt_payload(thread_id) if paused else None,
        "proposed": state.get("proposed"),
    }


def run_graph(question: str, thread_id: str | None = None) -> dict[str, Any]:
    thread_id = thread_id or str(uuid.uuid4())
    with span("graph", question=question[:80]):
        compiled_graph.invoke({"question": question}, _thread_config(thread_id))
        snapshot = compiled_graph.get_state(_thread_config(thread_id))
        paused = bool(snapshot.next)
        return _pack(dict(snapshot.values), thread_id, paused)


def resume_graph(thread_id: str, action: str, proposed: dict[str, Any] | None = None) -> dict[str, Any]:
    decision = {"action": action, "proposed": proposed}
    with span("hitl_resume", action=action):
        compiled_graph.invoke(Command(resume=decision), _thread_config(thread_id))
        snapshot = compiled_graph.get_state(_thread_config(thread_id))
        paused = bool(snapshot.next)
        return _pack(dict(snapshot.values), thread_id, paused)
