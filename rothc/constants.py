"""
Physical and chemical constants used in the RothC model.
"""


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
