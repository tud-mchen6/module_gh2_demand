import pandas as pd
import glob
import os


def get_historical_per_capita_TFC(
        inputs : str,
        population_input : str,
        output_dir : str,
        output_file : str,
):
    """
    Get historical values of per capita total final energy consumption of each country.
    Using IEA energy balance data, and match the year with the population year.

    Parameters:
    - inputs: str - Paths to the energy balances country-specific CSV files.
    - population_input: str - Path to the extracted population number for the specific
        year of the energy balances.
    - output_dir: str - Path to save the calculated CSV file.
    - output_file: str - Path of the final output file.

    Unit: GJ/capita, unit conversion performed as energy balance data is in TJ
    """

    dict_all = {'ISO3':[], 'TFC_per_capita':[]}

    for filepath in list(inputs):
        # Extract country name from the filepath, hard-coded
        country = filepath.replace(".csv", "").split('_')[-2]
        df = pd.read_csv(filepath)
        TFC_country = df[(df['flow']=='TFC') & (df['product']=='TOTAL')]['value'].values[0]
        # Get population data
        population_country = pd.read_csv(population_input, index_col=0)
        population_country = population_country.at[country, 'population']
        TFC_per_capita = TFC_country / population_country * 1e3 # Switch unit
        dict_all['ISO3'].append(country)
        dict_all['TFC_per_capita'].append(TFC_per_capita)
        
    
    os.makedirs(output_dir, exist_ok=True)
    pd.DataFrame.from_dict(dict_all).to_csv(output_file, index=False)


if __name__ == "__main__":
    get_historical_per_capita_TFC(
        inputs=snakemake.input.inputs,
        population_input=snakemake.input.population_input,
        output_dir=snakemake.params.output_dir,
        output_file=snakemake.output.output_file,
    )