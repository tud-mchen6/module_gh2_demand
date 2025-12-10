import pandas as pd
import os


def process_countries_hydro_nuclear_prod(inputs : str, countries, output_dir : str, output_file : str,
                                         year: int):
    """
    Processes IEA electricity balance CSV files for specified countries to extract hydropower and nuclear
    electricity production (final output).

    Parameters:
    - inputs: A collection of paths to the directory containing country-level IEA energy balance CSV files.
    - countries: list - List of country codes to process, given in ISO3 codes.
    - output_dir: str - Path of the directory to save the target file.
    - output_file: str - Path to save the processed one CSV file.
    - year: int - The year to get production data from.

    Unit: GWh, converted into TJ

    """

    # Hard-coded list of sectors and carriers
    flow_labels = ['EHYDRO', 'EHNUCLEAR']

    # Iterate over countries
    for country, file_path in zip(countries, inputs):
        df = pd.read_csv(file_path)
        # Step 1. Get electricity production by carrier of the given year
        df_year = df[(df['year'] == year) & (df['product']=='ELECTR')]
        df_year = df_year.pivot(index='short', columns='flow', values='value').fillna(0)
        # Step 2. Get the hydro and nuclear output
        # Sum up electricity production from all carriers
        df_year['HYDRO_NUCLEAR'] = 0
        for flow_label in flow_labels:
            if flow_label in df_year:
                df_year['HYDRO_NUCLEAR'] += df_year[flow_label]
        # Convert from GWh to TJ
        df_year['HYDRO_NUCLEAR'] *= 3600 / 1e3
        # Add country code
        df_year['ISO3'] = country
        # Append the current country to the total countries dataframe
        if country == countries[0]:
            df_all = df_year
        else:
            df_all = pd.concat([df_all, df_year], ignore_index=True)

    # Do some cleaning
    df_all = df_all[['ISO3', 'HYDRO_NUCLEAR']].fillna(0).round(4)

    # Create the folder to keep the processed csv
    os.makedirs(output_dir, exist_ok=True)
    df_all.to_csv(output_file, index=False)


    

if __name__ == "__main__":
    process_countries_hydro_nuclear_prod(
        inputs=list(snakemake.input),
        countries = snakemake.params.countries,
        output_dir=snakemake.params.output_dir,
        output_file=snakemake.output.output_file,
        year=snakemake.params.year,
    )

