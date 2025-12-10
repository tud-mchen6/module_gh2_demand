import pandas as pd
import os


def process_countries_TFC_sectors(inputs : str, countries, output_dir : str, output_file : str,):
    """
    Processes IEA energy balance CSV files for specified countries to extract Total Final Consumption (TFC) by sector.

    Parameters:
    - inputs: A collection of paths to the directory containing country-level IEA energy balance CSV files.
    - countries: list - List of country codes to process, given in ISO3 codes.
    - output_file: str - Path to save the processed one CSV file.
    """

    # Calculate the share of TFC by sector for each country
    # Note: List of sectors is hard-coded as not every country has all sectors
    list_sectors = ['TOTIND', 'TOTTRANS', 'RESIDENT', 'COMMPUB', 'AGRICULT', 'FISHING', 'ONONSPEC', 'NONENUSE']
    # Iterate through all the countries selected
    df_all = pd.DataFrame()
    for country, file_path in zip(countries, inputs):
        df = pd.read_csv(file_path)
        df_sectors = df[df['flow'].isin(list_sectors)]
        # Calculate the share of each sector's TFC in the iterated country
        df_sector_totalTFC = df_sectors[df_sectors['product'] == 'TOTAL'].pivot(index='short', columns='flow', values='value')
        df_sector_totalTFC['ISO3'] = country
        # Append the current country to the total countries dataframe
        if country == countries[0]:
            df_all = df_sector_totalTFC
        else:
            df_all = pd.concat([df_all, df_sector_totalTFC], ignore_index=True)
    df_all['CALC_TOTAL'] = df_all[list_sectors].sum(axis=1)
    for sector in list_sectors:
        df_all[f'SHARE_{sector}'] = df_all[sector] / df_all['CALC_TOTAL']
        del df_all[sector]
        df_all = df_all.rename(columns={f'SHARE_{sector}' : sector})
    del df_all['CALC_TOTAL']
    # Do some cleaning
    df_all = df_all.fillna(0).round(4)

    # Create the folder to keep the processed csv
    os.makedirs(output_dir, exist_ok=True)
    df_all.to_csv(output_file, index=False)

    

if __name__ == "__main__":
    process_countries_TFC_sectors(
        inputs=list(snakemake.input),
        countries = snakemake.params.countries,
        output_dir=snakemake.params.output_dir,
        output_file=snakemake.output.output_file,
    )

