"""
RothC Python Implementation
============================

The Rothamsted Carbon Model: RothC
Developed by David Jenkinson and Kevin Coleman

Python translation by Alice Milne, Jonah Prout and Kevin Coleman (29/02/2024)

This package implements the RothC soil carbon model for simulating the turnover of 
organic carbon in non-waterlogged topsoil.

References:
    Coleman, K., and Jenkinson, D.S. (2014) RothC - A Model for the Turnover of 
    Carbon in Soil. Model description and users guide (updated June 2014)
"""

from .constants import ModelConstants
from .data_structures import CarbonPools, SoilProperties, ClimateData, CarbonInputs
from .rate_modifiers import RateModifiers
from .decomposition import DecompositionModel
from .model import RothCModel
from .data_handler import DataHandler
from .runner import ModelRunner

__version__ = "1.0.0"
__author__ = "Alice Milne, Jonah Prout, Kevin Coleman"

__all__ = [
    'ModelConstants',
    'CarbonPools',
    'SoilProperties',
    'ClimateData',
    'CarbonInputs',
    'RateModifiers',
    'DecompositionModel',
    'RothCModel',
    'DataHandler',
    'ModelRunner',
]
