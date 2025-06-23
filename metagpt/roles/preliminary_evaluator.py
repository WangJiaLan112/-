#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/3/11 15:04
@Author  : czr
@File    : artist.py
"""
from metagpt.actions import BossRequirement
from metagpt.actions import Assess
from metagpt.roles import Role


class PreliminaryEvaluator(Role):
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
        name: str = 'Preliminary Evaluator', 
        profile: str = '医学专业人士，具备丰富的医疗知识和临床经验，能够对患者的初步信息进行全面评估。', 
        goal: str = '根据患者的病史、症状和身体基本数据，提供一份关于患者的报告，为后续医生的深入诊断提供基础。', 
        constraints: str = "", 
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
        self._init_actions([Assess])
        self._watch([BossRequirement])
