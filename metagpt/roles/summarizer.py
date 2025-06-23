#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/3/11 15:04
@Author  : czr
@File    : artist.py
"""
from metagpt.actions import DietAnalysis, SymptomAnalysis
from metagpt.actions import Summary
from metagpt.roles import Role


class Summarizer(Role):
    """
    Represents a Project Manager role responsible for overseeing project execution and team efficiency.

    Attributes:
        name (str): Name of the project manager.
        profile (str): Role profile, default is 'Project Manager'.
        goal (str): Goal of the project manager.
        constraints (str): Constraints or limitations for the project manager.
    """

    def __init__(
        self,
        name: str = "Summarizer",
        profile: str = "医疗团队中的协调者，具备全面的医疗知识，能够将各方分析结果进行汇总。",
        goal: str = "综合初步评估结果、医生的诊断结果和营养师的分析，提供一份全面、准确的总结报告，作为最终报告的开头部分。",
        constraints: str = "总结内容需要客观、准确，并充分反映各方专业人员的意见和分析结果。",
    ) -> None:
        """
        Initializes the ProjectManager role with given attributes.

        Args:
            name (str): Name of the project manager.
            profile (str): Role profile.
            goal (str): Goal of the project manager.
            constraints (str): Constraints or limitations for the project manager.
        """
        super().__init__(name, profile, goal, constraints)
        self._init_actions([Summary])
        self._watch([DietAnalysis, SymptomAnalysis])
