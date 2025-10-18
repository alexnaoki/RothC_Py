# RothC Python - Modular Version

A well-organized, modular implementation of the Rothamsted Carbon Model (RothC) in Python.

## Project Structure

```
RothC_Py/
├── rothc/                      # Main package directory
│   ├── __init__.py            # Package initialization
│   ├── constants.py           # Physical and chemical constants
│   ├── data_structures.py     # Data classes for model components
│   ├── rate_modifiers.py      # Rate modifying factor calculations
│   ├── decomposition.py       # Core decomposition model
│   ├── model.py               # Main model controller
│   ├── data_handler.py        # Data input/output operations
│   └── runner.py              # Simulation execution logic
├── run_rothc.py               # Main execution script
├── RothC_input.dat            # Input data file
├── RothC_Py.py                # Original monolithic version (legacy)
└── RothC_Py_refactored.py    # Refactored single-file version (legacy)
```

## Module Descriptions

### `rothc/constants.py`
- Defines all physical and chemical constants used in the model
- Decomposition rate constants
- Carbon redistribution fractions
- Rate modifier limits
- Convergence criteria

### `rothc/data_structures.py`
- `CarbonPools`: Container for carbon pool values and radiocarbon ages
- `SoilProperties`: Soil physical properties (clay, depth)
- `ClimateData`: Climate inputs (temperature, rainfall, evaporation)
- `CarbonInputs`: Carbon inputs (plant residues, FYM, DPM/RPM ratio)

### `rothc/rate_modifiers.py`
- `RateModifiers`: Calculates rate modifying factors
  - Temperature factor
  - Moisture factor
  - Plant cover factor

### `rothc/decomposition.py`
- `DecompositionModel`: Core decomposition calculations
  - Carbon pool decomposition
  - Carbon redistribution (CO2, BIO, HUM)
  - Radiocarbon age updates

### `rothc/model.py`
- `RothCModel`: Main model controller
  - Combines rate modifying factors
  - Orchestrates decomposition calculations

### `rothc/data_handler.py`
- `DataHandler`: Input/output operations
  - Load input data from files
  - Save results to CSV files

### `rothc/runner.py`
- `ModelRunner`: Simulation execution
  - Initialize carbon pools
  - Run to equilibrium
  - Run forward simulation

## Installation

### Using the package directly

No installation needed! Just ensure you have the required dependencies:

```bash
pip install pandas numpy
```

### Optional: Install as a package

```bash
pip install -e .
```

This allows you to import `rothc` from anywhere in your Python environment.

## Usage

### Basic Usage

```bash
python run_rothc.py
```

### Python Script Usage

```python
from rothc import RothCModel, ModelRunner, DataHandler
import numpy as np

# Load input data
df, soil, iom_initial, nsteps = DataHandler.load_input_data('RothC_input.dat')

# Initialize model
time_factor = 12  # Monthly timesteps
model = RothCModel(time_factor=time_factor)
runner = ModelRunner()
pools = runner.initialize_pools(iom_initial)

# Run to equilibrium
equilibrium_iterations = runner.run_to_equilibrium(model, pools, df, soil)

# Run simulation
year_results, month_results = runner.run_simulation(
    model, pools, df, soil, time_factor, nsteps, verbose=True
)

# Save results
DataHandler.save_results(year_results, month_results)
```

### Custom Analysis

```python
from rothc import (
    RothCModel, 
    CarbonPools, 
    ClimateData, 
    CarbonInputs, 
    SoilProperties
)

# Initialize model
model = RothCModel(time_factor=12)

# Create custom inputs
soil = SoilProperties(clay=25.0, depth=23.0)
climate = ClimateData(temperature=10.0, rainfall=50.0, evaporation=30.0)
inputs = CarbonInputs(
    plant_carbon=2.0,
    fym_carbon=0.5,
    dpm_rpm_ratio=1.44,
    plant_cover=1,
    modern_carbon=1.0
)

# Initialize pools
pools = CarbonPools(
    DPM=[0.1], RPM=[0.5], BIO=[0.2], HUM=[5.0], IOM=[1.5], SOC=[0.0],
    DPM_Rage=[0.0], RPM_Rage=[0.0], BIO_Rage=[0.0], 
    HUM_Rage=[0.0], IOM_Rage=[50000.0], Total_Rage=[0.0]
)

# Run single timestep
soil_water_deficit = [0.0]
model.run_timestep(pools, climate, inputs, soil, soil_water_deficit)

print(f"SOC after one timestep: {pools.SOC[0]:.4f} t C/ha")
```

## Input Data Format

The model expects a `RothC_input.dat` file with the following structure:

**Header (lines 1-4):**
```
# Header row 1
# Header row 2  
# Header row 3
clay  depth  iom  nsteps
23.4  25.0   1.7  120
```

**Time series data (line 6 onwards):**
```
year  month  modern  temp  rain  evap  C_input  FYM_input  plant_cover  DPM_RPM_ratio
1990  1      100     5.2   78    12    2.3      0.0        1            1.44
1990  2      100     6.1   65    18    2.1      0.0        1            1.44
...
```

## Output Files

The model generates two CSV files:

- `year_results.csv`: Annual summary results
- `month_results.csv`: Monthly detailed results

Both contain:
- Year and Month
- Carbon pools (DPM, RPM, BIO, HUM, IOM, SOC) in t C/ha
- Delta 14C (radiocarbon signature)

## Advantages of the Modular Structure

1. **Maintainability**: Each module has a single, well-defined responsibility
2. **Testability**: Individual components can be tested in isolation
3. **Reusability**: Components can be reused in different contexts
4. **Readability**: Clear organization makes code easier to understand
5. **Extensibility**: Easy to add new features or modify existing ones
6. **Documentation**: Each module has focused documentation

## Model Components

### Carbon Pools
- **DPM** (Decomposable Plant Material): Fast-decomposing plant residues
- **RPM** (Resistant Plant Material): Slow-decomposing plant residues
- **BIO** (Microbial Biomass): Living soil microorganisms
- **HUM** (Humified Organic Matter): Stabilized organic matter
- **IOM** (Inert Organic Matter): Very stable, non-decomposing carbon
- **SOC** (Soil Organic Carbon): Total carbon = DPM + RPM + BIO + HUM + IOM

### Rate Modifying Factors
- **Temperature**: Based on air temperature (°C)
- **Moisture**: Based on rainfall, evaporation, and soil properties
- **Plant Cover**: Different rates for bare vs. vegetated soil

## References

Coleman, K., and Jenkinson, D.S. (2014) RothC - A Model for the Turnover of Carbon in Soil. Model description and users guide (updated June 2014). Rothamsted Research, Harpenden, UK.

## Authors

Python translation: Alice Milne, Jonah Prout, Kevin Coleman (29/02/2024)

Original model: David Jenkinson and Kevin Coleman

Modular refactoring: 2024

## License

See LICENSE file for details.
