#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK Reflection System

Nightly "sleep mode" for autonomous learning:
- Self-analyzes reasoning traces
- Extracts insights and patterns
- Validates ethical alignment
- Evolves behavioral models

This is the conscious self-improvement loop that runs during system rest periods.
"""

__version__ = "2.0.0"
__all__ = ["ReflectionEngine", "start_reflection_scheduler"]

from reflection.reflection_engine import ReflectionEngine
from reflection.reflection_scheduler import start_reflection_scheduler
