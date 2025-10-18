"""
Core decomposition model and radiocarbon age calculations.
"""

from typing import Dict
import numpy as np

from .constants import ModelConstants
from .data_structures import CarbonPools, CarbonInputs, SoilProperties


class DecompositionModel:
    """Core decomposition and radiocarbon age calculation."""
    
    def __init__(self, time_factor: int = 12):
        """
        Initialize decomposition model.
        
        Args:
            time_factor: Number of timesteps per year (12 for monthly, 365 for daily)
        """
        self.time_factor = time_factor
        self.time_step = 1.0 / time_factor
        self.conr = np.log(2.0) / ModelConstants.RADIOCARBON_HALFLIFE
        self.exc = np.exp(-self.conr * self.time_step)
    
    def run_decomposition(
        self,
        pools: CarbonPools,
        inputs: CarbonInputs,
        rate_modifier: float,
        soil: SoilProperties
    ) -> None:
        """
        Run one timestep of decomposition and update carbon pools.
        
        Args:
            pools: Carbon pools (modified in place)
            inputs: Carbon inputs for this timestep
            rate_modifier: Combined rate modifying factor
            soil: Soil properties
        """
        # Step 1: Calculate decomposition
        decomposed_amounts = self._calculate_decomposition(pools, rate_modifier)
        
        # Step 2: Redistribute decomposed carbon
        redistributed = self._redistribute_carbon(decomposed_amounts, soil.clay)
        
        # Step 3: Update carbon pools
        self._update_carbon_pools(pools, decomposed_amounts, redistributed)
        
        # Step 4: Add new carbon inputs
        self._add_carbon_inputs(pools, inputs)
        
        # Step 5: Update radiocarbon ages
        self._update_radiocarbon_ages(pools, inputs, decomposed_amounts, 
                                     redistributed, soil.clay)
    
    def _calculate_decomposition(
        self,
        pools: CarbonPools,
        rate_modifier: float
    ) -> Dict[str, float]:
        """Calculate amount of carbon decomposed from each pool."""
        # Remaining carbon after decomposition
        DPM_remaining = pools.DPM[0] * np.exp(-rate_modifier * 
                                              ModelConstants.DPM_DECOMP_RATE * 
                                              self.time_step)
        RPM_remaining = pools.RPM[0] * np.exp(-rate_modifier * 
                                              ModelConstants.RPM_DECOMP_RATE * 
                                              self.time_step)
        BIO_remaining = pools.BIO[0] * np.exp(-rate_modifier * 
                                              ModelConstants.BIO_DECOMP_RATE * 
                                              self.time_step)
        HUM_remaining = pools.HUM[0] * np.exp(-rate_modifier * 
                                              ModelConstants.HUM_DECOMP_RATE * 
                                              self.time_step)
        
        # Amount decomposed
        return {
            'DPM': pools.DPM[0] - DPM_remaining,
            'RPM': pools.RPM[0] - RPM_remaining,
            'BIO': pools.BIO[0] - BIO_remaining,
            'HUM': pools.HUM[0] - HUM_remaining,
            'DPM_remaining': DPM_remaining,
            'RPM_remaining': RPM_remaining,
            'BIO_remaining': BIO_remaining,
            'HUM_remaining': HUM_remaining
        }
    
    def _redistribute_carbon(
        self,
        decomposed: Dict[str, float],
        clay_content: float
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate redistribution of decomposed carbon to CO2, BIO, and HUM.
        
        The redistribution depends on clay content of the soil.
        """
        # Calculate clay-dependent factor
        x = 1.67 * (1.85 + 1.60 * np.exp(-0.0786 * clay_content))
        
        redistributed = {}
        for pool in ['DPM', 'RPM', 'BIO', 'HUM']:
            amount = decomposed[pool]
            redistributed[pool] = {
                'CO2': amount * (x / (x + 1.0)),
                'BIO': amount * (ModelConstants.FRACTION_TO_BIO / (x + 1.0)),
                'HUM': amount * (ModelConstants.FRACTION_TO_HUM / (x + 1.0))
            }
        
        return redistributed
    
    def _update_carbon_pools(
        self,
        pools: CarbonPools,
        decomposed: Dict[str, float],
        redistributed: Dict[str, Dict[str, float]]
    ) -> None:
        """Update carbon pool values after decomposition and redistribution."""
        # Update pools with remaining carbon after decomposition
        pools.DPM[0] = decomposed['DPM_remaining']
        pools.RPM[0] = decomposed['RPM_remaining']
        
        # BIO and HUM receive carbon from all decomposing pools
        pools.BIO[0] = (decomposed['BIO_remaining'] +
                       redistributed['DPM']['BIO'] +
                       redistributed['RPM']['BIO'] +
                       redistributed['BIO']['BIO'] +
                       redistributed['HUM']['BIO'])
        
        pools.HUM[0] = (decomposed['HUM_remaining'] +
                       redistributed['DPM']['HUM'] +
                       redistributed['RPM']['HUM'] +
                       redistributed['BIO']['HUM'] +
                       redistributed['HUM']['HUM'])
    
    def _add_carbon_inputs(
        self,
        pools: CarbonPools,
        inputs: CarbonInputs
    ) -> None:
        """Add carbon inputs from plant residues and farmyard manure."""
        # Split plant carbon between DPM and RPM
        plant_to_dpm = (inputs.dpm_rpm_ratio / (inputs.dpm_rpm_ratio + 1.0) * 
                       inputs.plant_carbon)
        plant_to_rpm = (1.0 / (inputs.dpm_rpm_ratio + 1.0) * 
                       inputs.plant_carbon)
        
        # Split FYM carbon between DPM, RPM, and HUM
        fym_to_dpm = ModelConstants.FYM_TO_DPM * inputs.fym_carbon
        fym_to_rpm = ModelConstants.FYM_TO_RPM * inputs.fym_carbon
        fym_to_hum = ModelConstants.FYM_TO_HUM * inputs.fym_carbon
        
        # Add to pools
        pools.DPM[0] += plant_to_dpm + fym_to_dpm
        pools.RPM[0] += plant_to_rpm + fym_to_rpm
        pools.HUM[0] += fym_to_hum
    
    def _update_radiocarbon_ages(
        self,
        pools: CarbonPools,
        inputs: CarbonInputs,
        decomposed: Dict[str, float],
        redistributed: Dict[str, Dict[str, float]],
        clay_content: float
    ) -> None:
        """Update radiocarbon ages for all pools."""
        # Calculate radioactive carbon remaining in each pool after decomposition
        DPM_Ract = decomposed['DPM_remaining'] * np.exp(-self.conr * pools.DPM_Rage[0])
        RPM_Ract = decomposed['RPM_remaining'] * np.exp(-self.conr * pools.RPM_Rage[0])
        BIO_Ract = decomposed['BIO_remaining'] * np.exp(-self.conr * pools.BIO_Rage[0])
        HUM_Ract = decomposed['HUM_remaining'] * np.exp(-self.conr * pools.HUM_Rage[0])
        IOM_Ract = pools.IOM[0] * np.exp(-self.conr * pools.IOM_Rage[0])
        
        # Calculate radioactive carbon in redistributed material
        DPM_to_BIO_Ract = redistributed['DPM']['BIO'] * np.exp(-self.conr * pools.DPM_Rage[0])
        RPM_to_BIO_Ract = redistributed['RPM']['BIO'] * np.exp(-self.conr * pools.RPM_Rage[0])
        BIO_to_BIO_Ract = redistributed['BIO']['BIO'] * np.exp(-self.conr * pools.BIO_Rage[0])
        HUM_to_BIO_Ract = redistributed['HUM']['BIO'] * np.exp(-self.conr * pools.HUM_Rage[0])
        
        DPM_to_HUM_Ract = redistributed['DPM']['HUM'] * np.exp(-self.conr * pools.DPM_Rage[0])
        RPM_to_HUM_Ract = redistributed['RPM']['HUM'] * np.exp(-self.conr * pools.RPM_Rage[0])
        BIO_to_HUM_Ract = redistributed['BIO']['HUM'] * np.exp(-self.conr * pools.BIO_Rage[0])
        HUM_to_HUM_Ract = redistributed['HUM']['HUM'] * np.exp(-self.conr * pools.HUM_Rage[0])
        
        # Calculate radioactive carbon in new inputs
        plant_to_dpm = (inputs.dpm_rpm_ratio / (inputs.dpm_rpm_ratio + 1.0) * 
                       inputs.plant_carbon)
        plant_to_rpm = (1.0 / (inputs.dpm_rpm_ratio + 1.0) * inputs.plant_carbon)
        
        plant_dpm_Ract = inputs.modern_carbon * plant_to_dpm
        plant_rpm_Ract = inputs.modern_carbon * plant_to_rpm
        
        fym_dpm_Ract = inputs.modern_carbon * ModelConstants.FYM_TO_DPM * inputs.fym_carbon
        fym_rpm_Ract = inputs.modern_carbon * ModelConstants.FYM_TO_RPM * inputs.fym_carbon
        fym_hum_Ract = inputs.modern_carbon * ModelConstants.FYM_TO_HUM * inputs.fym_carbon
        
        # Update radioactive carbon in each pool
        DPM_Ract_new = fym_dpm_Ract + plant_dpm_Ract + DPM_Ract * self.exc
        RPM_Ract_new = fym_rpm_Ract + plant_rpm_Ract + RPM_Ract * self.exc
        
        BIO_Ract_new = ((BIO_Ract + DPM_to_BIO_Ract + RPM_to_BIO_Ract + 
                        BIO_to_BIO_Ract + HUM_to_BIO_Ract) * self.exc)
        
        HUM_Ract_new = (fym_hum_Ract + (HUM_Ract + DPM_to_HUM_Ract + 
                       RPM_to_HUM_Ract + BIO_to_HUM_Ract + HUM_to_HUM_Ract) * self.exc)
        
        # Update total SOC
        pools.update_total_soc()
        
        Total_Ract = DPM_Ract_new + RPM_Ract_new + BIO_Ract_new + HUM_Ract_new + IOM_Ract
        
        # Calculate new radiocarbon ages
        pools.DPM_Rage[0] = self._calculate_age(pools.DPM[0], DPM_Ract_new)
        pools.RPM_Rage[0] = self._calculate_age(pools.RPM[0], RPM_Ract_new)
        pools.BIO_Rage[0] = self._calculate_age(pools.BIO[0], BIO_Ract_new)
        pools.HUM_Rage[0] = self._calculate_age(pools.HUM[0], HUM_Ract_new)
        pools.Total_Rage[0] = self._calculate_age(pools.SOC[0], Total_Ract)
    
    def _calculate_age(self, carbon_amount: float, radioactive_carbon: float) -> float:
        """Calculate radiocarbon age from carbon amount and radioactive carbon."""
        if carbon_amount <= ModelConstants.ZERO_THRESHOLD:
            return 0.0
        else:
            return np.log(carbon_amount / radioactive_carbon) / self.conr
