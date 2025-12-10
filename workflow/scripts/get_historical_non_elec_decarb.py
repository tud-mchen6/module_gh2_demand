import pandas as pd
import requests
import os
from io import StringIO



def process_countries_non_elec_decarb(inputs : str, countries, heat_decarb : str, output_dir : str, output_file : str, year: int = 2023):
    """
    Processes IEA energy balance CSV files for specified countries to calculate decarbonisation 
    level of non-electricity energy consumed in each sector of each country.

    Unit of data: TJ

    Parameters:
    - inputs: A collection of paths to the directory containing country-level IEA energy balance CSV files.
    - countries: list - List of country codes to process, given in ISO3 codes.
    - heat_decarb: str - Path to the processed heat decarbonisation level CSV file.
    - output_dir: str - Directory to save the processed one CSV file.
    - output_file: str - Path to save the processed one CSV file.
    - year: int - The year to process the data for.

    """

    # Hard-coded list of carriers
    list_nonCarb_nonElec_carriers = ['GEOTHERM', 'COMRENEW']
    list_carriers = ['COAL', 'CRNGFEED', 'MTOTOIL', 'NATGAS', 'GEOTHERM', 'COMRENEW', 'HEAT']
    # Hard-coded list of sectors
    list_sectors = ['TOTIND', 'TOTTRANS', 'RESIDENT', 'COMMPUB', 'AGRICULT', 'FISHING', 'ONONSPEC', 'NONENUSE']
    # Read in the heat decarbonisation level data
    df_heat_decarb = pd.read_csv(heat_decarb)
    df_all = pd.DataFrame(columns=['ISO3'] + list_sectors)

    # Iterate over countries
    for country, file_path in zip(countries, inputs):
        df = pd.read_csv(file_path)
        df_year = df[df['year'] == year]
        # Iterate over sectors
        flows = df_year['flow'].unique()
        for sector in list_sectors:
            if sector not in flows:
                continue
            df_sector_non_elec = df_year[(df_year['flow'] == sector) & ~(df_year['product'].isin(['ELECTR','TOTAL']))]
            # Overcome data bugs in the API: double entry for 'Oil and oil products' and 'Oil products'.
            # Therefore, if the data values are the same for both carriers, they are seen as one carrier only.
            if ('MTOTOIL' in df_sector_non_elec['product'].unique()) & ('TOTPRODS' in df_sector_non_elec['product'].unique()):
                if (df_sector_non_elec[df_sector_non_elec['product']=='MTOTOIL']['value'].values[0]==
                 df_sector_non_elec[df_sector_non_elec['product']=='TOTPRODS']['value'].values[0]):
                    df_sector_non_elec.loc[df_sector_non_elec['product'] == 'MTOTOIL', 'value'] = 0
            # Calculate total TFC that is not electricity
            sector_tot_TFC = df_sector_non_elec['value'].sum()
            # Calculate the decarbonised TFC: non-carbon carriers + decarbonised heat
            nonCarb_TFC = 0
            # Non-carbon non-electricity carriers
            for carrier in list_nonCarb_nonElec_carriers:
                if carrier in df_sector_non_elec['product'].values:
                    nonCarb_TFC += df_sector_non_elec[df_sector_non_elec['product'] == carrier]['value'].values[0]
            # If heat is present, apply the decarbonisation level
            if 'HEAT' in df_sector_non_elec['product'].values:
                if df_heat_decarb[df_heat_decarb['ISO3'] == country]['HEAT_DECARB'].values[0] > 0:
                    heat_decarb_level = df_heat_decarb[df_heat_decarb['ISO3'] == country]['HEAT_DECARB'].values[0]
                    nonCarb_TFC += df_sector_non_elec[df_sector_non_elec['product'] == 'HEAT']['value'].values[0] * heat_decarb_level
            df_all.loc[country, sector] = nonCarb_TFC / sector_tot_TFC if sector_tot_TFC > 0 else 0
        df_all.loc[country, 'ISO3'] = country
        

    # Do some cleaning
    # Move the country code to the front of the dataframe
    df_all = df_all[['ISO3'] + [c for c in df_all.columns if c != 'ISO3']]
    df_all = df_all.set_index('ISO3')
    df_all = df_all.fillna(0).round(4)

    # Create the folder to keep the processed csv
    os.makedirs(output_dir, exist_ok=True)
    df_all.to_csv(output_file)


    

if __name__ == "__main__":
    process_countries_non_elec_decarb(
        inputs=list(snakemake.input),
        countries = snakemake.params.countries,
        heat_decarb=snakemake.input.heat_decarb,
        output_dir=snakemake.params.output_dir,
        output_file=snakemake.output.output_file,
        year=snakemake.params.year,
    )

