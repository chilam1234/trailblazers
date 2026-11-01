from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from trailblazers.store import store

_exporter = InMemorySpanExporter()
_provider = TracerProvider(resource=Resource.create({"service.name": "trailblazers"}))
_provider.add_span_processor(SimpleSpanProcessor(_exporter))
trace.set_tracer_provider(_provider)
tracer = trace.get_tracer("trailblazers")


@contextmanager
def span(name: str, **attrs: Any) -> Iterator[Any]:
    started = time.perf_counter()
    with tracer.start_as_current_span(name) as current:
        for key, value in attrs.items():
            if value is not None:
                current.set_attribute(key, value)
        try:
            yield current
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000
            current.set_attribute("elapsed_ms", round(elapsed_ms, 3))
            store.record_trace(
                {
                    "name": name,
                    "elapsed_ms": round(elapsed_ms, 3),
                    "attrs": {k: v for k, v in attrs.items() if v is not None},
                }
            )


def recent_otel_spans(limit: int = 40) -> list[dict[str, Any]]:
    spans = list(_exporter.get_finished_spans())[-limit:]
    out = []
    for item in reversed(spans):
        out.append(
            {
                "name": item.name,
                "elapsed_ms": item.attributes.get("elapsed_ms"),
                "attrs": dict(item.attributes),
            }
        )
    return out
