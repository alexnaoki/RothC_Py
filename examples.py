#!/usr/bin/env python3
"""
Example script demonstrating various uses of the modular RothC package.

This script shows how to:
1. Run a basic simulation
2. Access individual model components
3. Perform custom analysis
4. Work with the data structures
"""

import numpy as np
import pandas as pd
from rothc import (
    ModelConstants,
    CarbonPools,
    SoilProperties,
    ClimateData,
    CarbonInputs,
    RateModifiers,
    DecompositionModel,
    RothCModel,
    DataHandler,
    ModelRunner,
)


def example_1_basic_simulation():
    """Example 1: Basic simulation using the standard workflow."""
    print("=" * 80)
    print("Example 1: Basic Simulation")
    print("=" * 80)
    print()
    
    # Load data
    df, soil, iom_initial, nsteps = DataHandler.load_input_data('RothC_input.dat')
    
    # Initialize
    model = RothCModel(time_factor=12)
    runner = ModelRunner()
    pools = runner.initialize_pools(iom_initial)
    
    # Run to equilibrium
    print("Running to equilibrium...")
    equilibrium_iterations = runner.run_to_equilibrium(model, pools, df, soil)
    print(f"Converged after {equilibrium_iterations} iterations\n")
    
    # Run forward simulation for first year only
    print("Running first year of simulation...")
    year_results, month_results = runner.run_simulation(
        model, pools, df, soil, 12, 24, verbose=False
    )
    
    print(f"Completed {len(month_results)} monthly timesteps")
    print(f"Final SOC: {pools.SOC[0]:.4f} t C/ha\n")


def example_2_custom_rate_modifiers():
    """Example 2: Calculate rate modifying factors manually."""
    print("=" * 80)
    print("Example 2: Custom Rate Modifier Calculations")
    print("=" * 80)
    print()
    
    rm = RateModifiers()
    
    # Test temperature factor at different temperatures
    temperatures = [-10, -5, 0, 5, 10, 15, 20, 25]
    print("Temperature Rate Modifying Factors:")
    print("-" * 40)
    for temp in temperatures:
        factor = rm.calculate_temperature_factor(temp)
        print(f"  {temp:>3}°C: {factor:.4f}")
    print()
    
    # Test moisture factor
    soil = SoilProperties(clay=23.4, depth=25.0)
    soil_water_deficit = [0.0]
    
    print("Moisture Rate Modifying Factors:")
    print("-" * 40)
    scenarios = [
        ("Wet month", 100, 20),
        ("Average month", 50, 40),
        ("Dry month", 20, 60),
    ]
    
    for name, rain, evap in scenarios:
        factor = rm.calculate_moisture_factor(
            rain, evap, soil, plant_cover=1, soil_water_deficit=soil_water_deficit.copy()
        )
        print(f"  {name:15s}: {factor:.4f}")
    print()


def example_3_single_timestep():
    """Example 3: Run a single timestep with custom inputs."""
    print("=" * 80)
    print("Example 3: Single Timestep Simulation")
    print("=" * 80)
    print()
    
    # Initialize model
    model = RothCModel(time_factor=12)
    
    # Create custom soil properties
    soil = SoilProperties(clay=25.0, depth=23.0)
    
    # Create custom climate data
    climate = ClimateData(
        temperature=12.0,
        rainfall=65.0,
        evaporation=35.0
    )
    
    # Create custom carbon inputs
    inputs = CarbonInputs(
        plant_carbon=2.5,
        fym_carbon=0.0,
        dpm_rpm_ratio=1.44,
        plant_cover=1,
        modern_carbon=1.0
    )
    
    # Initialize pools with some carbon
    pools = CarbonPools(
        DPM=[0.5], RPM=[2.0], BIO=[1.0], HUM=[10.0], IOM=[1.5], SOC=[0.0],
        DPM_Rage=[0.0], RPM_Rage=[0.0], BIO_Rage=[0.0], 
        HUM_Rage=[0.0], IOM_Rage=[50000.0], Total_Rage=[0.0]
    )
    pools.update_total_soc()
    
    print(f"Initial SOC: {pools.SOC[0]:.4f} t C/ha")
    print(f"  DPM: {pools.DPM[0]:.4f}")
    print(f"  RPM: {pools.RPM[0]:.4f}")
    print(f"  BIO: {pools.BIO[0]:.4f}")
    print(f"  HUM: {pools.HUM[0]:.4f}")
    print(f"  IOM: {pools.IOM[0]:.4f}")
    print()
    
    # Run one timestep
    soil_water_deficit = [0.0]
    model.run_timestep(pools, climate, inputs, soil, soil_water_deficit)
    
    print(f"After 1 month:")
    print(f"Final SOC: {pools.SOC[0]:.4f} t C/ha")
    print(f"  DPM: {pools.DPM[0]:.4f}")
    print(f"  RPM: {pools.RPM[0]:.4f}")
    print(f"  BIO: {pools.BIO[0]:.4f}")
    print(f"  HUM: {pools.HUM[0]:.4f}")
    print(f"  IOM: {pools.IOM[0]:.4f}")
    print(f"Change: {pools.SOC[0] - 15.0:+.4f} t C/ha\n")


def example_4_decomposition_details():
    """Example 4: Access detailed decomposition information."""
    print("=" * 80)
    print("Example 4: Detailed Decomposition Analysis")
    print("=" * 80)
    print()
    
    # Create decomposition model
    decomp = DecompositionModel(time_factor=12)
    
    # Initialize pools
    pools = CarbonPools(
        DPM=[1.0], RPM=[3.0], BIO=[1.5], HUM=[8.0], IOM=[1.5], SOC=[0.0],
        DPM_Rage=[0.0], RPM_Rage=[0.0], BIO_Rage=[0.0], 
        HUM_Rage=[0.0], IOM_Rage=[50000.0], Total_Rage=[0.0]
    )
    
    # Calculate decomposition amounts
    rate_modifier = 1.0  # No environmental constraints
    decomposed = decomp._calculate_decomposition(pools, rate_modifier)
    
    print("Decomposition amounts (1 month with rate modifier = 1.0):")
    print("-" * 60)
    print(f"  DPM: {pools.DPM[0]:.4f} → {decomposed['DPM_remaining']:.4f} "
          f"(decomposed: {decomposed['DPM']:.4f})")
    print(f"  RPM: {pools.RPM[0]:.4f} → {decomposed['RPM_remaining']:.4f} "
          f"(decomposed: {decomposed['RPM']:.4f})")
    print(f"  BIO: {pools.BIO[0]:.4f} → {decomposed['BIO_remaining']:.4f} "
          f"(decomposed: {decomposed['BIO']:.4f})")
    print(f"  HUM: {pools.HUM[0]:.4f} → {decomposed['HUM_remaining']:.4f} "
          f"(decomposed: {decomposed['HUM']:.4f})")
    print()
    
    # Show redistribution
    soil = SoilProperties(clay=23.4, depth=25.0)
    redistributed = decomp._redistribute_carbon(decomposed, soil.clay)
    
    print("Redistribution of decomposed DPM:")
    print("-" * 60)
    print(f"  To CO2: {redistributed['DPM']['CO2']:.4f} t C/ha")
    print(f"  To BIO: {redistributed['DPM']['BIO']:.4f} t C/ha")
    print(f"  To HUM: {redistributed['DPM']['HUM']:.4f} t C/ha")
    print()


def example_5_constants_and_parameters():
    """Example 5: Access model constants and parameters."""
    print("=" * 80)
    print("Example 5: Model Constants and Parameters")
    print("=" * 80)
    print()
    
    print("Decomposition rate constants (per year):")
    print("-" * 60)
    print(f"  DPM: {ModelConstants.DPM_DECOMP_RATE}")
    print(f"  RPM: {ModelConstants.RPM_DECOMP_RATE}")
    print(f"  BIO: {ModelConstants.BIO_DECOMP_RATE}")
    print(f"  HUM: {ModelConstants.HUM_DECOMP_RATE}")
    print()
    
    print("Carbon redistribution fractions:")
    print("-" * 60)
    print(f"  To BIO: {ModelConstants.FRACTION_TO_BIO}")
    print(f"  To HUM: {ModelConstants.FRACTION_TO_HUM}")
    print()
    
    print("FYM carbon split:")
    print("-" * 60)
    print(f"  To DPM: {ModelConstants.FYM_TO_DPM}")
    print(f"  To RPM: {ModelConstants.FYM_TO_RPM}")
    print(f"  To HUM: {ModelConstants.FYM_TO_HUM}")
    print()
    
    print("Rate modifier limits:")
    print("-" * 60)
    print(f"  Moisture max: {ModelConstants.RMF_MOISTURE_MAX}")
    print(f"  Moisture min: {ModelConstants.RMF_MOISTURE_MIN}")
    print(f"  Plant cover (bare): {ModelConstants.RMF_PLANT_COVER_BARE}")
    print(f"  Plant cover (vegetated): {ModelConstants.RMF_PLANT_COVER_VEGETATED}")
    print()


def main():
    """Run all examples."""
    print("\n")
    print("*" * 80)
    print("*" + " " * 78 + "*")
    print("*" + " " * 20 + "RothC Python - Usage Examples" + " " * 28 + "*")
    print("*" + " " * 78 + "*")
    print("*" * 80)
    print("\n")
    
    # Run examples
    try:
        example_5_constants_and_parameters()
        example_2_custom_rate_modifiers()
        example_4_decomposition_details()
        example_3_single_timestep()
        # example_1_basic_simulation()  # Uncomment if you have RothC_input.dat
        
    except FileNotFoundError:
        print("\nNote: Some examples require 'RothC_input.dat' to be present.")
        print("Place your input file in the current directory to run all examples.\n")
    
    print("\n")
    print("*" * 80)
    print("*" + " " * 78 + "*")
    print("*" + " " * 25 + "Examples Complete!" + " " * 32 + "*")
    print("*" + " " * 78 + "*")
    print("*" * 80)
    print("\n")


if __name__ == "__main__":
    main()
