"""Nucleo de PyIntruder: logica pura, sin dependencias de interfaz."""

from .attacks import count_requests, generate_assignments
from .engine import AttackEngine
from .http_client import parse_raw_request, send_request
from .template import RequestTemplate

__all__ = [
    "RequestTemplate",
    "generate_assignments",
    "count_requests",
    "parse_raw_request",
    "send_request",
    "AttackEngine",
]
