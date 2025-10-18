"""
Model runner for executing RothC simulations.
"""

import os
from typing import List, Tuple
import numpy as np
import pandas as pd

from .constants import ModelConstants
from .data_structures import CarbonPools, SoilProperties, ClimateData, CarbonInputs
from .model import RothCModel


class ModelRunner:
    """Run RothC model simulation."""
    
    def __init__(self, input_directory: str = None):
        """
        Initialize model runner.
        
        Args:
            input_directory: Directory containing input files (optional)
        """
        self.input_directory = input_directory
        if input_directory:
            os.chdir(input_directory)
    
    def initialize_pools(self, iom_value: float) -> CarbonPools:
        """
        Initialize carbon pools to zero (except IOM).
        
        Args:
            iom_value: Initial inert organic matter value
            
        Returns:
            Initialized carbon pools
        """
        return CarbonPools(
            DPM=[0.0], RPM=[0.0], BIO=[0.0], HUM=[0.0], 
            IOM=[iom_value], SOC=[0.0],
            DPM_Rage=[0.0], RPM_Rage=[0.0], BIO_Rage=[0.0], 
            HUM_Rage=[0.0], IOM_Rage=[50000.0], Total_Rage=[0.0]
        )
    
    def run_to_equilibrium(
        self,
        model: RothCModel,
        pools: CarbonPools,
        df: pd.DataFrame,
        soil: SoilProperties,
        tolerance: float = ModelConstants.EQUILIBRIUM_TOLERANCE
    ) -> int:
        """
        Run model to equilibrium state.
        
        Args:
            model: RothC model instance
            pools: Carbon pools (modified in place)
            df: Input data frame
            soil: Soil properties
            tolerance: Convergence tolerance
            
        Returns:
            Number of iterations to reach equilibrium
        """
        soil_water_deficit = [0.0]
        pools.update_total_soc()
        
        print(f"Initial state: DPM={pools.DPM[0]:.4f}, RPM={pools.RPM[0]:.4f}, "
              f"BIO={pools.BIO[0]:.4f}, HUM={pools.HUM[0]:.4f}, "
              f"IOM={pools.IOM[0]:.4f}, SOC={pools.SOC[0]:.4f}")
        
        k = 0  # Index for cycling through yearly data
        j = 0  # Total iteration counter
        toc_previous = 0.0
        test = 100.0
        
        while test > tolerance:
            # Get data for this timestep
            climate = ClimateData(
                temperature=df.t_tmp[k],
                rainfall=df.t_rain[k],
                evaporation=df.t_evap[k]
            )
            
            inputs = CarbonInputs(
                plant_carbon=df.t_C_Inp[k],
                fym_carbon=df.t_FYM_Inp[k],
                dpm_rpm_ratio=df.t_DPM_RPM[k],
                plant_cover=int(df.t_PC[k]),
                modern_carbon=df.t_mod[k] / 100.0
            )
            
            # Run one timestep
            model.run_timestep(pools, climate, inputs, soil, soil_water_deficit)
            
            # Check for convergence at end of each year
            if (k + 1) % model.time_factor == 0:
                toc_current = pools.DPM[0] + pools.RPM[0] + pools.BIO[0] + pools.HUM[0]
                test = abs(toc_current - toc_previous)
                toc_previous = toc_current
                k = 0  # Reset to beginning of year
            else:
                k += 1
            
            j += 1
            
            # Safety check to prevent infinite loops
            if j > 1000000:
                print("Warning: Maximum iterations reached before convergence")
                break
        
        total_delta = (np.exp(-pools.Total_Rage[0] / 8035.0) - 1.0) * 1000.0
        print(f"\nEquilibrium reached after {j} iterations:")
        print(f"DPM={pools.DPM[0]:.4f}, RPM={pools.RPM[0]:.4f}, "
              f"BIO={pools.BIO[0]:.4f}, HUM={pools.HUM[0]:.4f}, "
              f"IOM={pools.IOM[0]:.4f}, SOC={pools.SOC[0]:.4f}, "
              f"Delta14C={total_delta:.2f}")
        
        return j
    
    def run_simulation(
        self,
        model: RothCModel,
        pools: CarbonPools,
        df: pd.DataFrame,
        soil: SoilProperties,
        start_step: int,
        n_steps: int,
        verbose: bool = True
    ) -> Tuple[List[List], List[List]]:
        """
        Run model simulation for specified time period.
        
        Args:
            model: RothC model instance
            pools: Carbon pools (modified in place)
            df: Input data frame
            soil: Soil properties
            start_step: Starting timestep index
            n_steps: Total number of timesteps
            verbose: Print progress information
            
        Returns:
            Tuple of (year_results, month_results)
        """
        soil_water_deficit = [0.0]
        month_results = []
        year_results = []
        
        for i in range(start_step, n_steps):
            # Get data for this timestep
            climate = ClimateData(
                temperature=df.t_tmp[i],
                rainfall=df.t_rain[i],
                evaporation=df.t_evap[i]
            )
            
            inputs = CarbonInputs(
                plant_carbon=df.t_C_Inp[i],
                fym_carbon=df.t_FYM_Inp[i],
                dpm_rpm_ratio=df.t_DPM_RPM[i],
                plant_cover=int(df.t_PC[i]),
                modern_carbon=df.t_mod[i] / 100.0
            )
            
            # Run one timestep
            model.run_timestep(pools, climate, inputs, soil, soil_water_deficit)
            
            # Calculate delta 14C
            total_delta = (np.exp(-pools.Total_Rage[0] / 8035.0) - 1.0) * 1000.0
            
            # Store monthly results
            month_results.append([
                int(df.loc[i, "t_year"]),
                int(df.loc[i, "t_month"]),
                pools.DPM[0],
                pools.RPM[0],
                pools.BIO[0],
                pools.HUM[0],
                pools.IOM[0],
                pools.SOC[0],
                total_delta
            ])
            
            # Store yearly results (at end of year)
            if df.t_month[i] == model.time_factor:
                year_results.append([
                    int(df.loc[i, "t_year"]),
                    int(df.loc[i, "t_month"]),
                    pools.DPM[0],
                    pools.RPM[0],
                    pools.BIO[0],
                    pools.HUM[0],
                    pools.IOM[0],
                    pools.SOC[0],
                    total_delta
                ])
                
                if verbose:
                    print(f"Year {int(df.loc[i, 't_year'])}: SOC={pools.SOC[0]:.4f} t C/ha")
        
        return year_results, month_results
