"""
Main RothC model controller.
"""

from typing import List

from .decomposition import DecompositionModel
from .rate_modifiers import RateModifiers
from .data_structures import CarbonPools, ClimateData, CarbonInputs, SoilProperties


class RothCModel:
    """Main RothC model controller."""
    
    def __init__(self, time_factor: int = 12):
        """
        Initialize RothC model.
        
        Args:
            time_factor: Number of timesteps per year (12 for monthly, 365 for daily)
        """
        self.time_factor = time_factor
        self.decomp_model = DecompositionModel(time_factor)
        self.rate_modifiers = RateModifiers()
    
    def run_timestep(
        self,
        pools: CarbonPools,
        climate: ClimateData,
        inputs: CarbonInputs,
        soil: SoilProperties,
        soil_water_deficit: List[float]
    ) -> None:
        """
        Run one timestep of the RothC model.
        
        Args:
            pools: Carbon pools (modified in place)
            climate: Climate data for this timestep
            inputs: Carbon inputs for this timestep
            soil: Soil properties
            soil_water_deficit: Soil water deficit (modified in place)
        """
        # Calculate rate modifying factors
        rm_temp = self.rate_modifiers.calculate_temperature_factor(climate.temperature)
        rm_moisture = self.rate_modifiers.calculate_moisture_factor(
            climate.rainfall, climate.evaporation, soil, 
            inputs.plant_cover, soil_water_deficit
        )
        rm_plant_cover = self.rate_modifiers.calculate_plant_cover_factor(
            inputs.plant_cover
        )
        
        # Combine rate modifiers
        combined_rate_modifier = rm_temp * rm_moisture * rm_plant_cover
        
        # Run decomposition
        self.decomp_model.run_decomposition(pools, inputs, combined_rate_modifier, soil)
