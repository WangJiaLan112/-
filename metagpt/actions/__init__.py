#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:44
@Author  : alexanderwu
@File    : __init__.py
"""
from enum import Enum

from metagpt.actions.action import Action
from metagpt.actions.action_output import ActionOutput
from metagpt.actions.add_requirement import BossRequirement
from metagpt.actions.assess import Assess
from metagpt.actions.diet_analysis import DietAnalysis
from metagpt.actions.summary import Summary
from metagpt.actions.symptom_analysis import SymptomAnalysis

class ActionType(Enum):
    """All types of Actions, used for indexing."""

    ADD_REQUIREMENT = BossRequirement
    ASSESS = Assess
    DIET_ANALYSIS = DietAnalysis
    SUMMARY = Summary
    SYMPTOM_AHALYSIS = SymptomAnalysis


__all__ = [
    "ActionType",
    "Action",
    "ActionOutput",
]
