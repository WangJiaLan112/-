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


class Doctor(Role):
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
        name: str = 'Doctor', 
        profile: str = '具备深厚的医学理论知识和实践经验，能够对患者的症状进行深入分析，提出准确的诊断和治疗方案。', 
        goal: str = '通过分析症状的性质、持续时间和严重程度，确定病因，并提供解决方案，决定是否建议患者去医院进一步检查。', 
        constraints: str = '诊断结果需要综合考虑患者的整体情况，包括初步评估结果。', 
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
        self._init_actions([SymptomAnalysis])
        self._watch([Assess,SymptomAnalysis,DietAnalysis])
