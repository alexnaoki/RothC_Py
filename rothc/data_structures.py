"""
Data structures for RothC model components.
"""

from typing import List
from dataclasses import dataclass


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
