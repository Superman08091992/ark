#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK ID Growth System

Adaptive behavioral modeling with confidence-weighted learning curves.
Links reflection insights to agent identity evolution.

Architecture:
- ID Model: Behavioral feature extraction and EWMA updates
- Features: Derive traits from reasoning traces and reflections
- Learning Curves: Confidence-weighted adaptation over time
- Integration: Consumes reflection insights for evolution

This system enables agents to learn and adapt their behavior based on
self-reflection and validated experiences.
"""

__version__ = "2.0.0"
__all__ = ["IDModel", "FeatureExtractor", "update_from_reflections"]

from id.model import IDModel
from id.features import FeatureExtractor, update_from_reflections
