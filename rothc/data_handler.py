"""
Data input/output handling for RothC model.
"""

from typing import List, Tuple
import pandas as pd

from .data_structures import SoilProperties


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
