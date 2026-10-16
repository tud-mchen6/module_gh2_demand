"""Rules to used to process the downloaded IEA energy balance data."""

import glob
import os

configfile: "config/config.yaml"

# scenario = config["scenario"]
# scenario_config = config["scenarios"][scenario]

# Get all available countries from IEA dataset
country_codes = pd.read_csv(workflow.source_path("../internal/country_codes.csv"))
requested_countries = country_codes.loc[country_codes['IEA'].notna(), 'ISO3'].tolist()
# Default processing year is 2023 unless specified in config
def get_scenario_config(scenario):
    return config["scenarios"][scenario]
def get_year(wildcards):
    return get_scenario_config(wildcards)["population_scenario"]
# The year to create the demand data for. The population of this year will be used
# to calculate the final demand.
def get_population_scenario(wildcards):
    return get_scenario_config(wildcards)["population_scenario"]

def get_population_ref_year(wildcards):
    return get_scenario_config(wildcards)["population_ref_year"]



rule get_historical_sector_TFC_share:
    message:
        """
        Get real-world total final energy consumption broken down by sector, 
        for {params.countries} from IEA energy balances, in year {params.year}.
        """
    params:
        countries=requested_countries,
        year=lambda wc: wc.year,
    input:
        input_dir="<resources>/automatic/IEA_energy_balances/{year}",
    output:
        output_file="<resources>/processed/IEA_historical_sector_TFC_share_{year}.csv"
    conda:
        "../envs/default.yaml"
    script:
        "../scripts/get_historical_TFC_bySector.py"


rule get_historical_sector_electrification:
    message:
        """
        Calculate real-world electrification rate of each sector, for {params.countries} 
        from IEA energy balances, in year {params.year}.
        """
    params:
        countries=requested_countries,
        year=lambda wc: wc.year,
    input:
        input_dir="<resources>/automatic/IEA_energy_balances/{year}",
    output:
        output_file="<resources>/processed/IEA_historical_sector_electrification_{year}.csv"
    conda:
        "../envs/default.yaml"
    script:
        "../scripts/get_historical_electrification_bySector.py"


rule get_historical_elec_decarb:
    message:
        "Calculate real-world electricity decarbonisation level, for {params.countries} from IEA energy balances."
    params:
        countries=requested_countries,
        year=lambda wc: wc.year,
    input:
        # The heat balance file contains data for both electricity and heat
        input_dir="<resources>/automatic/IEA_elec_heat_balances/{year}",
    output:
        output_file="<resources>/processed/IEA_historical_elec_decarb_{year}.csv"
    conda:
        "../envs/default.yaml"
    script:
        "../scripts/get_historical_elec_decarb.py"


rule get_historical_heat_decarb:
    message:
        "Calculate real-world heat decarbonisation level, for {params.countries} from IEA heat balances."
    params:
        countries=requested_countries,
        year=lambda wc: wc.year,
    input:
        input_dir="<resources>/automatic/IEA_elec_heat_balances/{year}",
    output:
        output_file="<resources>/processed/IEA_historical_heat_decarb_{year}.csv"
    conda:
        "../envs/default.yaml"
    script:
        "../scripts/get_historical_heat_decarb.py"


rule get_historical_non_elec_decarb:
    message:
        """
        Calculate real-world non-electricity decarbonisation level in each sector, for {params.countries} 
        from IEA energy balances.
        """
    params:
        countries=requested_countries,
        year=lambda wc: wc.year,
    input:
        input_dir="<resources>/automatic/IEA_energy_balances/{year}",
        heat_decarb="<resources>/processed/IEA_historical_heat_decarb_{year}.csv"
    output:
        output_file="<resources>/processed/IEA_historical_non_elec_decarb_{year}.csv"

    conda:
        "../envs/default.yaml"
    script:
        "../scripts/get_historical_non_elec_decarb.py"


rule get_historical_other_renewables_prod:
    message:
        """
        Get real-world other renewables electricity production such as hydro and nuclear, for {params.countries} from 
        IEA electricity balances by carrier data for year {params.year}.
        """
    params:
        countries=requested_countries,
        year=lambda wc: wc.year,
    input:
        input_dir="<resources>/automatic/IEA_elec_heat_balances/{year}",
    output:
        output_file="<resources>/processed/IEA_historical_other_renewables_prod_{year}.csv"
    conda:
        "../envs/default.yaml"
    script:
        "../scripts/get_historical_other_renewables_prod.py"


rule get_historical_non_elec_renew_consum:
    message:
        """
        Get real-world non-electricity final consumption, including biomass, waste, and other renewables,
        for {params.countries} from IEA energy balances by carrier data for year {params.year}.
        """
    params:
        countries=requested_countries,
        year=lambda wc: wc.year,
    input:
        input_dir="<resources>/automatic/IEA_energy_balances/{year}",
        heat_decarb="<resources>/processed/IEA_historical_heat_decarb_{year}.csv",
    output:
        output_file="<resources>/processed/IEA_historical_non_elec_renew_consum_{year}.csv"

    conda:
        "../envs/default.yaml"
    script:
        "../scripts/get_historical_non_elec_renew_consum.py"


rule get_population:
    message:
        """
        Given population reference year, get the clean by-country population file for final calculation.
        """
    input:
        population_file="<resources>/automatic/WPP_population/WPP_population_{population_scenario}.csv",
    output:
        population_output="<resources>/processed/population_{population_scenario}_{year}.csv",
    params:
        population_ref_year=lambda wc: wc.year,
        output_dir="<resources>/processed/",
    conda:
        "../envs/default.yaml"
    script:
        "../scripts/get_population.py"


rule get_historical_per_capita_TFC:
    message:
        """
        Use the population data of the same historical year as TFC data to calculate the per capita TFC
        in each country.
        """
    params:
        countries=requested_countries,
        year=lambda wc: wc.year,
    input:
        input_dir="<resources>/automatic/IEA_energy_balances/{year}",
        population_input="<resources>/processed/population_Medium_{year}.csv",
    output:
        output_file="<resources>/processed/IEA_historical_per_capita_TFC_{year}.csv",
    conda:
        "../envs/default.yaml"
    script:
        "../scripts/get_historical_per_capita_TFC.py"


rule get_historical_elec_TnD_loss_rate:
    message:
        """
        Calculate the transmission & distribution loss rates of each country based on historical data.
        """
    params:
        countries=requested_countries,
        year=lambda wc: wc.year,
    input:
        input_dir="<resources>/automatic/IEA_elec_heat_balances/{year}",
    output:
        output_file="<resources>/processed/IEA_historical_elec_TnD_loss_rate_{year}.csv",
    conda:
        "../envs/default.yaml"
    script:
        "../scripts/get_historical_elec_TnD_loss_rate.py"