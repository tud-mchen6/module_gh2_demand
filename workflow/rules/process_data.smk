"""Rules to used to process the downloaded IEA energy balance data."""

import glob
import os

configfile: "config/config.yaml"

# If default_countries is True, get all available countries from IEA dataset
if config["required"]["download_default_countries"]:
    country_codes = pd.read_csv("workflow/internal/country_codes.csv")
    available_countries = country_codes.loc[country_codes['IEA'].notna(), 'ISO3'].tolist()
# If config defines specific countries, use those; otherwise use all found ones
requested_countries = (config.get("optional") or {}).get("countries") or available_countries
# Default processing year is 2023 unless specified in config
year = (config.get("optional") or {}).get("year_for_IEA_balance") or 2023
# The year to create the demand data for. The population of this year will be used
# to calculate the final demand.
population_ref_year = config["required"]["population_ref_year"]
population_scenario = config["required"]["population_scenario"]

# Validate that all requested countries exist
missing = [c for c in requested_countries if c not in available_countries]
if missing:
    sys.exit(f"Error: requested countries not found in workspace: {missing}")



rule get_historical_sector_TFC_share:
    message:
        """
        Get real-world total final energy consumption broken down by sector, 
        for {params.countries} from IEA energy balances, in year {year}.
        """
    input:
        expand("resources/automatic/IEA_energy_balances/IEA_EnergyBalance_{country}_{year}.csv", 
        country=requested_countries, year=year)
    output:
        output_file="resources/processed/IEA_historical_sector_TFC_share_{year}.csv"
    params:
        countries=requested_countries,
        output_dir="resources/processed/"
    script:
        "../scripts/get_historical_TFC_bySector.py"


rule get_historical_sector_electrification:
    message:
        """
        Calculate real-world electrification rate of each sector, for {params.countries} 
        from IEA energy balances, in year {year}.
        """
    input:
        expand("resources/automatic/IEA_energy_balances/IEA_EnergyBalance_{country}_{year}.csv", 
        country=requested_countries, year=year)
    output:
        output_file="resources/processed/IEA_historical_sector_electrification_{year}.csv"
    params:
        countries=requested_countries,
        output_dir="resources/processed/"
    script:
        "../scripts/get_historical_electrification_bySector.py"


rule get_historical_elec_decarb:
    message:
        "Calculate real-world electricity decarbonisation level, for {params.countries} from IEA energy balances."
    input:
        expand("resources/automatic/IEA_elec_heat_balances/IEA_elec_heat_balances_{country}_{year}.csv", 
        country=requested_countries, year=year)
    output:
        output_file="resources/processed/IEA_historical_elec_decarb_{year}.csv"
    params:
        countries=requested_countries,
        output_dir="resources/processed/",
        year=year
    script:
        "../scripts/get_historical_elec_decarb.py"


rule get_historical_heat_decarb:
    message:
        "Calculate real-world heat decarbonisation level, for {params.countries} from IEA heat balances."
    input:
        expand("resources/automatic/IEA_elec_heat_balances/IEA_elec_heat_balances_{country}_{year}.csv", 
        country=requested_countries, year=year)
    output:
        output_file="resources/processed/IEA_historical_heat_decarb_{year}.csv"
    params:
        countries=requested_countries,
        output_dir="resources/processed/",
        year=year
    script:
        "../scripts/get_historical_heat_decarb.py"


rule get_historical_non_elec_decarb:
    message:
        """
        Calculate real-world non-electricity decarbonisation level in each sector, for {params.countries} 
        from IEA energy balances.
        """
    input:
        expand("resources/automatic/IEA_energy_balances/IEA_EnergyBalance_{country}_{year}.csv", 
        country=requested_countries, year=year),
        heat_decarb="resources/processed/IEA_historical_heat_decarb_{year}.csv"
    output:
        output_file="resources/processed/IEA_historical_non_elec_decarb_{year}.csv"
    params:
        countries=requested_countries,
        output_dir="resources/processed/",
        year=year
    script:
        "../scripts/get_historical_non_elec_decarb.py"


rule get_historical_hydro_nuclear_prod:
    message:
        """
        Get real-world hydro and nuclear electricity production, for {params.countries} from 
        IEA electricity balances by carrier data for year {year}.
        """
    input:
        expand("resources/automatic/IEA_elec_heat_balances/IEA_elec_heat_balances_{country}_{year}.csv", 
        country=requested_countries, year=year),
    output:
        output_file="resources/processed/IEA_historical_hydro_nuclear_prod_{year}.csv"
    params:
        countries=requested_countries,
        output_dir="resources/processed/",
        year=year
    script:
        "../scripts/get_historical_hydro_nuclear_prod.py"


rule get_population:
    message:
        """
        Given population reference year, get the clean by-country population file for final calculation.
        """
    input:
        population_file=lambda wc: (f"resources/automatic/WPP_population/WPP_population_{population_scenario}.csv"),
    output:
        population_output="resources/processed/population_{year}.csv",
    params:
        population_ref_year=lambda wildcards: wildcards.year,
        output_dir="resources/processed/",
    script:
        "../scripts/get_population.py"


rule get_historical_per_capita_TFC:
    message:
        """
        Use the population data of the same historical year as TFC data to calculate the per capita TFC
        in each country.
        """
    input:
        inputs=expand("resources/automatic/IEA_energy_balances/IEA_EnergyBalance_{country}_{year}.csv", 
        country=requested_countries, year=year),
        population_input="resources/processed/population_{year}.csv",
    output:
        output_file="resources/processed/historical_per_capita_TFC_{year}.csv",
    params:
        output_dir="resources/processed/",
    script:
        "../scripts/get_historical_per_capita_TFC.py"


rule get_historical_elec_TnD_loss_rate:
    message:
        """
        Calculate the transmission & distribution loss rates of each country based on historical data.
        """
    input:
        inputs=expand("resources/automatic/IEA_elec_heat_balances/IEA_elec_heat_balances_{country}_{year}.csv", 
        country=requested_countries, year=year),
    output:
        output_file="resources/processed/IEA_historical_elec_TnD_loss_rate_{year}.csv",
    params:
        output_dir="resources/processed/",
    script:
        "../scripts/get_historical_elec_TnD_loss_rate.py"