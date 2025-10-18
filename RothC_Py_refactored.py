"""
RothC Python Implementation
============================

The Rothamsted Carbon Model: RothC
Developed by David Jenkinson and Kevin Coleman

Python translation by Alice Milne, Jonah Prout and Kevin Coleman (29/02/2024)

This module implements the RothC soil carbon model for simulating the turnover of 
organic carbon in non-waterlogged topsoil.

References:
    Coleman, K., and Jenkinson, D.S. (2014) RothC - A Model for the Turnover of 
    Carbon in Soil. Model description and users guide (updated June 2014)
"""

import os
from typing import List, Tuple, Dict
from dataclasses import dataclass
import pandas as pd
import numpy as np


# ============================================================================
# CONSTANTS
# ============================================================================

class ModelConstants:
    """Physical and chemical constants used in RothC model."""
    
    # Decomposition rate constants (per year for monthly timestep)
    DPM_DECOMP_RATE = 10.0      # Decomposable Plant Material
    RPM_DECOMP_RATE = 0.3       # Resistant Plant Material
    BIO_DECOMP_RATE = 0.66      # Microbial Biomass
    HUM_DECOMP_RATE = 0.02      # Humified Organic Matter
    
    # Radiocarbon decay constant
    RADIOCARBON_HALFLIFE = 5568.0  # years (Libby half-life)
    
    # FYM (Farmyard Manure) carbon split fractions
    FYM_TO_DPM = 0.49
    FYM_TO_RPM = 0.49
    FYM_TO_HUM = 0.02
    
    # Carbon pool redistribution fractions
    FRACTION_TO_BIO = 0.46
    FRACTION_TO_HUM = 0.54
    
    # Rate modifying factor limits
    RMF_MOISTURE_MAX = 1.0
    RMF_MOISTURE_MIN = 0.2
    RMF_PLANT_COVER_BARE = 1.0
    RMF_PLANT_COVER_VEGETATED = 0.6
    
    # Soil moisture constants
    SMD_DEPTH_ADJUSTMENT = 23.0  # cm
    SMD_1BAR_FRACTION = 0.444
    SMD_BARE_FRACTION = 0.556
    
    # Numerical threshold
    ZERO_THRESHOLD = 1e-8
    
    # Convergence criteria
    EQUILIBRIUM_TOLERANCE = 1e-6


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class CarbonPools:
    """Container for carbon pool values and their radiocarbon ages."""
    DPM: List[float]           # Decomposable Plant Material (t C/ha)
    RPM: List[float]           # Resistant Plant Material (t C/ha)
    BIO: List[float]           # Microbial Biomass (t C/ha)
    HUM: List[float]           # Humified Organic Matter (t C/ha)
    IOM: List[float]           # Inert Organic Matter (t C/ha)
    SOC: List[float]           # Total Soil Organic Carbon (t C/ha)
    
    DPM_Rage: List[float]      # Radiocarbon age of DPM (years)
    RPM_Rage: List[float]      # Radiocarbon age of RPM (years)
    BIO_Rage: List[float]      # Radiocarbon age of BIO (years)
    HUM_Rage: List[float]      # Radiocarbon age of HUM (years)
    IOM_Rage: List[float]      # Radiocarbon age of IOM (years)
    Total_Rage: List[float]    # Radiocarbon age of total SOC (years)
    
    def update_total_soc(self) -> None:
        """Update total SOC from individual pools."""
        self.SOC[0] = self.DPM[0] + self.RPM[0] + self.BIO[0] + self.HUM[0] + self.IOM[0]


@dataclass
class SoilProperties:
    """Container for soil physical properties."""
    clay: float        # Clay content (%)
    depth: float       # Topsoil depth (cm)
    

@dataclass
class ClimateData:
    """Container for climate input data."""
    temperature: float      # Air temperature (°C)
    rainfall: float         # Rainfall (mm)
    evaporation: float      # Open pan evaporation (mm)
    

@dataclass
class CarbonInputs:
    """Container for carbon input data."""
    plant_carbon: float     # Plant residue carbon input (t C/ha)
    fym_carbon: float       # Farmyard manure carbon input (t C/ha)
    dpm_rpm_ratio: float    # Ratio of DPM to RPM in plant inputs
    plant_cover: int        # Plant cover flag (0=bare, 1=vegetated)
    modern_carbon: float    # Fraction modern carbon (for radiocarbon)


# ============================================================================
# RATE MODIFYING FACTORS
# ============================================================================

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


# ============================================================================
# DECOMPOSITION CORE
# ============================================================================

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


# ============================================================================
# MAIN MODEL CONTROLLER
# ============================================================================

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


# ============================================================================
# DATA INPUT/OUTPUT
# ============================================================================

class DataHandler:
    """Handle data input and output for RothC model."""
    
    @staticmethod
    def load_input_data(input_file: str = 'RothC_input.dat') -> Tuple[pd.DataFrame, SoilProperties, float, int]:
        """
        Load RothC input data from file.
        
        Args:
            input_file: Path to input data file
            
        Returns:
            Tuple of (time series data, soil properties, initial IOM, number of steps)
        """
        # Read header information
        df_head = pd.read_csv(input_file, skiprows=3, header=0, nrows=1, 
                             index_col=None, delim_whitespace=True)
        
        # Extract soil properties
        soil = SoilProperties(
            clay=df_head.loc[0, "clay"],
            depth=df_head.loc[0, "depth"]
        )
        iom_initial = df_head.loc[0, "iom"]
        nsteps = int(df_head.loc[0, "nsteps"])
        
        # Read time series data
        df = pd.read_csv(input_file, skiprows=6, header=0, 
                        index_col=None, delim_whitespace=True)
        df.columns = ['t_year', 't_month', 't_mod', 't_tmp', 't_rain', 't_evap', 
                     't_C_Inp', 't_FYM_Inp', 't_PC', 't_DPM_RPM']
        
        return df, soil, iom_initial, nsteps
    
    @staticmethod
    def save_results(
        year_results: List[List],
        month_results: List[List],
        year_output_file: str = 'year_results.csv',
        month_output_file: str = 'month_results.csv'
    ) -> None:
        """
        Save model results to CSV files.
        
        Args:
            year_results: Annual results data
            month_results: Monthly results data
            year_output_file: Output file for annual results
            month_output_file: Output file for monthly results
        """
        columns = ["Year", "Month", "DPM_t_C_ha", "RPM_t_C_ha", "BIO_t_C_ha", 
                  "HUM_t_C_ha", "IOM_t_C_ha", "SOC_t_C_ha", "deltaC"]
        
        output_years = pd.DataFrame(year_results, columns=columns)
        output_months = pd.DataFrame(month_results, columns=columns)
        
        output_years.to_csv(year_output_file, index=False)
        output_months.to_csv(month_output_file, index=False)
        
        print(f"Results saved to {year_output_file} and {month_output_file}")


# ============================================================================
# MODEL RUNNER
# ============================================================================

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


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    
    print("="*80)
    print("RothC Python Model - Refactored Version")
    print("="*80)
    print()
    
    # Set up paths
    print(f"Current working directory: {os.getcwd()}")
    
    # Uncomment and modify the following line to change to your data directory:
    # os.chdir("/path/to/your/data/directory")
    
    # Load input data
    print("Loading input data...")
    df, soil, iom_initial, nsteps = DataHandler.load_input_data('RothC_input.dat')
    print(f"Loaded {len(df)} timesteps")
    print(f"Soil properties: clay={soil.clay}%, depth={soil.depth}cm")
    print(f"Initial IOM: {iom_initial} t C/ha")
    print()
    
    # Initialize model and pools
    time_factor = 12  # Monthly timesteps
    model = RothCModel(time_factor=time_factor)
    pools = ModelRunner().initialize_pools(iom_initial)
    runner = ModelRunner()
    
    # Run to equilibrium
    print("Running to equilibrium...")
    print("-" * 80)
    equilibrium_iterations = runner.run_to_equilibrium(model, pools, df, soil)
    print()
    
    # Store equilibrium results
    total_delta = (np.exp(-pools.Total_Rage[0] / 8035.0) - 1.0) * 1000.0
    year_results = [[1, equilibrium_iterations, pools.DPM[0], pools.RPM[0], 
                    pools.BIO[0], pools.HUM[0], pools.IOM[0], pools.SOC[0], 
                    total_delta]]
    
    # Run simulation
    print("Running simulation...")
    print("-" * 80)
    year_sim, month_sim = runner.run_simulation(
        model, pools, df, soil, time_factor, nsteps, verbose=True
    )
    
    # Combine results
    year_results.extend(year_sim)
    
    # Save results
    print()
    print("Saving results...")
    DataHandler.save_results(year_results, month_sim)
    
    print()
    print("="*80)
    print("Simulation complete!")
    print("="*80)


if __name__ == "__main__":
    main()
