"""Rules to used to download automatic resource files."""

import pandas as pd


configfile: "config/config.yaml"

# The year to get energy balance or electricity balance data from IEA
year = (config.get("optional") or {}).get("year_for_IEA_balance") or 2023
if not config["required"]["download_default_countries"]:
    requested_countries = config.get("optional", {}).get("countries")
else:
    # If default_countries is True, get all available countries from IEA dataset
    country_codes = pd.read_csv("workflow/internal/country_codes.csv")
    requested_countries = country_codes.loc[country_codes['IEA'].notna(), 'ISO3'].tolist()
population_scenario = config["required"]["population_scenario"]


rule download_balances_IEA:
    message:
        "Download the Energy Balances file per country of year {year} from IEA."
    params:
        year=year
    input:
        country_codes_file="workflow/internal/country_codes.csv",
    output:
        output_dir=directory("<resources>/automatic/IEA_energy_balances/"),
    conda:
        "../envs/shell.yaml"
    script:
        "../scripts/download_balances_IEA.py"



rule download_elec_heat_balances_IEA:
    message:
        """
        Download the electricity and heat balance file per country for year {year} until latest from IEA.

        This dataset includes electricity generated from all sources, already accounting for the 
        generation efficiencies. The data given in energy balances with 'Electricity plants', 
        instead, does not account for efficiencies but only the consumption of primal energy carriers,
        such as coal.
        """
    params:
        year=year
    input:
        country_codes_file="workflow/internal/country_codes.csv",
    output:
        output_dir=directory("<resources>/automatic/IEA_elec_heat_balances/"),
    conda:
        "../envs/shell.yaml"
    script:
        "../scripts/download_elec_heat_balances_IEA.py"



rule download_population_WPP:
    message:
        """
        Download per-country population data from the United Nations World Population Prospects,
        and perform slight processing on scenario and years.
        """
    params:
        population_scenario=population_scenario,
    output:
        output_file="<resources>/automatic/WPP_population/WPP_population_{population_scenario}.csv"
        # touch("resources/automatic/WPP_population/download_complete.flag")
    script:
        "../scripts/download_population_WPP.py"