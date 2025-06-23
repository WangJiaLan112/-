#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/3/11 15:04
@Author  : czr
@File    : artist.py
"""
from metagpt.actions import Assess
from metagpt.actions import SymptomAnalysis, DietAnalysis
from metagpt.roles import Role


class Nutritionist(Role):
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
        name: str = "Nutritionist",
        profile: str = "营养学专家，具备专业的营养学知识和实践经验，能够对患者的饮食习惯进行深入分析。",
        goal: str = "通过分析患者的饮食史、生活方式和近期饮食习惯的变化，提供个性化的饮食建议。",
        constraints: str = "饮食建议需要结合患者的整体健康状况进行制定。",
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
        self._init_actions([DietAnalysis])
        self._watch([Assess,SymptomAnalysis,DietAnalysis])
