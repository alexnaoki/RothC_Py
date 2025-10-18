"""
Rate modifying factors for decomposition.
"""

from typing import List
import numpy as np

from .constants import ModelConstants
from .data_structures import SoilProperties


class RateModifiers:
    """Calculate rate modifying factors for decomposition."""
    
    @staticmethod
    def calculate_temperature_factor(temperature: float) -> float:
        """
        Calculate rate modifying factor for temperature.
        
        Args:
            temperature: Air temperature in °C
            
        Returns:
            Temperature rate modifier (0.0 to ~5.0)
        """
        if temperature < -5.0:
            return 0.0
        else:
            return 47.91 / (np.exp(106.06 / (temperature + 18.27)) + 1.0)
    
    @staticmethod
    def calculate_moisture_factor(
        rainfall: float,
        evaporation: float,
        soil: SoilProperties,
        plant_cover: int,
        soil_water_deficit: List[float]
    ) -> float:
        """
        Calculate rate modifying factor for soil moisture.
        
        Args:
            rainfall: Monthly rainfall (mm)
            evaporation: Monthly open pan evaporation (mm)
            soil: Soil properties
            plant_cover: Plant cover flag (0=bare, 1=vegetated)
            soil_water_deficit: Soil water deficit list [mm] (modified in place)
            
        Returns:
            Moisture rate modifier (0.0 to 1.0)
        """
        # Calculate maximum soil moisture deficit
        SMDMax = -(20.0 + 1.3 * soil.clay - 0.01 * (soil.clay ** 2))
        SMDMaxAdj = SMDMax * soil.depth / ModelConstants.SMD_DEPTH_ADJUSTMENT
        
        # Calculate threshold values
        SMD1bar = ModelConstants.SMD_1BAR_FRACTION * SMDMaxAdj
        SMDBare = ModelConstants.SMD_BARE_FRACTION * SMDMaxAdj
        
        # Calculate drainage factor
        drainage_factor = rainfall - 0.75 * evaporation
        
        # Update soil water deficit
        min_swc_df = np.min([0.0, soil_water_deficit[0] + drainage_factor])
        min_smd_bare_swc = np.min([SMDBare, soil_water_deficit[0]])
        
        if plant_cover == 1:
            soil_water_deficit[0] = np.max([SMDMaxAdj, min_swc_df])
        else:
            soil_water_deficit[0] = np.max([min_smd_bare_swc, min_swc_df])
        
        # Calculate moisture rate modifier
        if soil_water_deficit[0] > SMD1bar:
            return ModelConstants.RMF_MOISTURE_MAX
        else:
            return (ModelConstants.RMF_MOISTURE_MIN + 
                   (ModelConstants.RMF_MOISTURE_MAX - ModelConstants.RMF_MOISTURE_MIN) * 
                   (SMDMaxAdj - soil_water_deficit[0]) / (SMDMaxAdj - SMD1bar))
    
    @staticmethod
    def calculate_plant_cover_factor(plant_cover: int) -> float:
        """
        Calculate rate modifying factor for plant cover.
        
        Args:
            plant_cover: Plant cover flag (0=bare, 1=vegetated)
            
        Returns:
            Plant cover rate modifier (0.6 or 1.0)
        """
        if plant_cover == 0:
            return ModelConstants.RMF_PLANT_COVER_BARE
        else:
            return ModelConstants.RMF_PLANT_COVER_VEGETATED
