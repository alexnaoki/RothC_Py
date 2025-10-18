# RothC Python - Quick Reference Guide

## 🚀 Quick Start (30 seconds)

```bash
# Navigate to directory
cd /Users/alexnaokiasatokobayashi/git/RothC_Py

# Run the model
python3 run_rothc.py
```

## 📁 File Structure Overview

```
rothc/                   # Package modules (import these)
├── constants.py        # Model parameters
├── data_structures.py  # Data containers
├── rate_modifiers.py   # Environmental factors
├── decomposition.py    # Core model
├── model.py           # Main controller
├── data_handler.py    # I/O operations
└── runner.py          # Simulation execution

run_rothc.py            # Standard simulation
examples.py             # Usage examples
setup.py               # Installation script
```

## 💡 Common Tasks

### Task 1: Run Standard Simulation
```python
python3 run_rothc.py
```

### Task 2: Import and Use Modules
```python
from rothc import RothCModel, DataHandler, ModelRunner

# Load data
df, soil, iom, nsteps = DataHandler.load_input_data('RothC_input.dat')

# Initialize and run
model = RothCModel(time_factor=12)
runner = ModelRunner()
pools = runner.initialize_pools(iom)
runner.run_to_equilibrium(model, pools, df, soil)
```

### Task 3: Custom Single Timestep
```python
from rothc import RothCModel, CarbonPools, ClimateData, CarbonInputs, SoilProperties

model = RothCModel(time_factor=12)
soil = SoilProperties(clay=25.0, depth=23.0)
climate = ClimateData(temperature=10.0, rainfall=50.0, evaporation=30.0)
inputs = CarbonInputs(plant_carbon=2.0, fym_carbon=0.0, dpm_rpm_ratio=1.44, 
                      plant_cover=1, modern_carbon=1.0)

pools = CarbonPools(DPM=[0.5], RPM=[2.0], BIO=[1.0], HUM=[10.0], IOM=[1.5], SOC=[0.0],
                    DPM_Rage=[0.0], RPM_Rage=[0.0], BIO_Rage=[0.0], 
                    HUM_Rage=[0.0], IOM_Rage=[50000.0], Total_Rage=[0.0])

swc = [0.0]
model.run_timestep(pools, climate, inputs, soil, swc)
print(f"SOC: {pools.SOC[0]:.4f} t C/ha")
```

### Task 4: Calculate Rate Modifiers
```python
from rothc import RateModifiers, SoilProperties

rm = RateModifiers()

# Temperature effect
temp_factor = rm.calculate_temperature_factor(15.0)  # 15°C

# Moisture effect
soil = SoilProperties(clay=23.4, depth=25.0)
swc = [0.0]
moisture_factor = rm.calculate_moisture_factor(
    rainfall=50.0, evaporation=30.0, soil=soil, 
    plant_cover=1, soil_water_deficit=swc
)

# Plant cover effect
cover_factor = rm.calculate_plant_cover_factor(plant_cover=1)

print(f"Combined: {temp_factor * moisture_factor * cover_factor:.4f}")
```

### Task 5: Access Model Constants
```python
from rothc import ModelConstants

print(f"DPM decay rate: {ModelConstants.DPM_DECOMP_RATE}")
print(f"RPM decay rate: {ModelConstants.RPM_DECOMP_RATE}")
print(f"BIO decay rate: {ModelConstants.BIO_DECOMP_RATE}")
print(f"HUM decay rate: {ModelConstants.HUM_DECOMP_RATE}")
```

## 📊 Key Classes Reference

### CarbonPools
```python
pools = CarbonPools(
    DPM=[0.0],        # Decomposable Plant Material (t C/ha)
    RPM=[0.0],        # Resistant Plant Material (t C/ha)
    BIO=[0.0],        # Microbial Biomass (t C/ha)
    HUM=[0.0],        # Humified Organic Matter (t C/ha)
    IOM=[1.5],        # Inert Organic Matter (t C/ha)
    SOC=[0.0],        # Total Soil Organic Carbon (t C/ha)
    DPM_Rage=[0.0],   # Radiocarbon age of DPM (years)
    RPM_Rage=[0.0],   # Radiocarbon age of RPM (years)
    BIO_Rage=[0.0],   # Radiocarbon age of BIO (years)
    HUM_Rage=[0.0],   # Radiocarbon age of HUM (years)
    IOM_Rage=[50000.0], # Radiocarbon age of IOM (years)
    Total_Rage=[0.0]  # Radiocarbon age of total SOC (years)
)
```

### SoilProperties
```python
soil = SoilProperties(
    clay=23.4,   # Clay content (%)
    depth=25.0   # Topsoil depth (cm)
)
```

### ClimateData
```python
climate = ClimateData(
    temperature=10.0,  # Air temperature (°C)
    rainfall=50.0,     # Rainfall (mm)
    evaporation=30.0   # Open pan evaporation (mm)
)
```

### CarbonInputs
```python
inputs = CarbonInputs(
    plant_carbon=2.0,    # Plant residue carbon (t C/ha)
    fym_carbon=0.5,      # Farmyard manure carbon (t C/ha)
    dpm_rpm_ratio=1.44,  # Ratio of DPM to RPM
    plant_cover=1,       # 0=bare, 1=vegetated
    modern_carbon=1.0    # Fraction modern C (for radiocarbon)
)
```

## 🔧 Model Parameters

### Decomposition Rates (per year)
- DPM: 10.0
- RPM: 0.3
- BIO: 0.66
- HUM: 0.02

### Carbon Redistribution
- To BIO: 46%
- To HUM: 54%
- To CO2: (remainder, clay-dependent)

### FYM Split
- To DPM: 49%
- To RPM: 49%
- To HUM: 2%

## 📝 Input File Format

`RothC_input.dat`:
```
# Comment line 1
# Comment line 2
# Comment line 3
clay  depth  iom  nsteps
23.4  25.0   1.7  120
# Data header
year  month  modern  temp  rain  evap  C_input  FYM_input  plant_cover  DPM_RPM_ratio
1990  1      100     5.2   78    12    2.3      0.0        1            1.44
```

## 🎯 Output Files

### year_results.csv
Annual summary: Year, Month, DPM, RPM, BIO, HUM, IOM, SOC, deltaC

### month_results.csv
Monthly detail: Year, Month, DPM, RPM, BIO, HUM, IOM, SOC, deltaC

## 🐛 Troubleshooting

### Import Error
```bash
# Make sure you're in the correct directory
cd /Users/alexnaokiasatokobayashi/git/RothC_Py

# Or install the package
pip install -e .
```

### File Not Found
```bash
# Check current directory
pwd

# Should show: /Users/alexnaokiasatokobayashi/git/RothC_Py
# Make sure RothC_input.dat is present
ls RothC_input.dat
```

### Module Not Found (numpy/pandas)
```bash
pip install numpy pandas
```

## 📚 Documentation Files

- **README_MODULAR.md** - Full documentation
- **STRUCTURE_SUMMARY.md** - Detailed module breakdown
- **QUICK_REFERENCE.md** - This file
- **examples.py** - 5 working examples

## 🔗 Module Dependencies

```
model.py
  ├─> decomposition.py
  │     ├─> constants.py
  │     └─> data_structures.py
  └─> rate_modifiers.py
        ├─> constants.py
        └─> data_structures.py

runner.py
  ├─> model.py
  ├─> constants.py
  └─> data_structures.py

data_handler.py
  └─> data_structures.py
```

## ⚡ Performance Tips

1. Use appropriate `time_factor`:
   - Monthly: `time_factor=12` (faster)
   - Daily: `time_factor=365` (more accurate)

2. Set `verbose=False` for faster runs:
   ```python
   runner.run_simulation(..., verbose=False)
   ```

3. Adjust equilibrium tolerance:
   ```python
   runner.run_to_equilibrium(..., tolerance=1e-5)  # Less strict
   ```

## 🎓 Learning Progression

1. ✅ Run `run_rothc.py` (understand basic workflow)
2. ✅ Read `README_MODULAR.md` (understand concepts)
3. ✅ Run `examples.py` (see usage patterns)
4. ✅ Import individual modules (build custom analysis)
5. ✅ Read source code (understand implementation)

## 📞 Getting Help

1. Check `README_MODULAR.md` for detailed docs
2. Run `examples.py` for working code
3. Read docstrings: `help(RothCModel)`
4. Check `STRUCTURE_SUMMARY.md` for architecture

## ✨ Key Takeaways

- **Import path**: `from rothc import ...`
- **Main script**: `run_rothc.py`
- **Examples**: `examples.py`
- **Data classes**: Use dataclasses for type safety
- **Constants**: Centralized in `ModelConstants`
- **Modular**: Import only what you need

---

**Last updated:** October 18, 2024
**Version:** 1.0.0
