#!/usr/bin/env python3
"""
Main execution script for RothC model.

This script runs the RothC soil carbon model simulation.
"""

import os
import numpy as np

from rothc import (
    RothCModel,
    ModelRunner,
    DataHandler
)


def main():
    """Main execution function."""
    
    print("="*80)
    print("RothC Python Model - Modular Version")
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
    runner = ModelRunner()
    pools = runner.initialize_pools(iom_initial)
    
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
