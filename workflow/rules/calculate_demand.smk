"""Rules to use user-provided parameters and in case of need, 
historical data to produce top-down electricity demand met by
variable renewable energy sources and green hydrogen."""

import glob
import os

configfile: "config/config.yaml"

# Get all available CSVs automatically
available_countries = [
    os.path.basename(f).split("_")[2]   # hard-coded, the part after the prefix
    for f in glob.glob("resources/automatic/IEA_energy_balances/IEA_EnergyBalance_*.csv")
]

scenario_name = config["required"]["scenario_name"]
ref_year = config.get("year_for_IEA_balance", []) or 2023
population_ref_year = config["required"]["population_ref_year"]


rule get_target_TFC_per_capita:
    message:
        """
        Prepare for the demand calculation by getting the target total final consumption
        per capita for each country.
        """
    params:
        countries=config.get("countries", []) or available_countries,
        country_overwrite=lambda wc: "resources/user/country_level_overwrite.csv" if os.path.exists("resources/user/country_level_overwrite.csv") else None,
        scenario_name=scenario_name,
        use_historical=config["required"]["historical_per_capita_TFC"],
        tot_per_capita_TFC=config["required"]["tot_per_capita_TFC"],
    input:
        reference_per_capita_TFC=lambda wc: (
            f"resources/processed/historical_per_capita_TFC_{ref_year}.csv"
        )
    conda:
        "../envs/default.yaml"
    output:
        output_file="resources/prepare/target_per_capita_TFC_{scenario_name}.csv"
    script:
        "../scripts/get_target_TFC_per_capita.py"


rule get_target_sector_TFC_share:
    message:
        """
        Prepare for the demand calculation by getting the target sector share in the
        total final consumption for each country.
        """
    params:
        countries=config.get("countries", []) or available_countries,
        ref_year=ref_year,
        sector_overwrite_dir="resources/user/sector_level_overwrite",
        scenario_name=scenario_name,
        use_historical=config["required"]["historical_sector_TFC_share"],
        country_overwrite=lambda wc: "resources/user/country_level_overwrite.csv" if os.path.exists("resources/user/country_level_overwrite.csv") else None,
    input:
        TFC_per_capita="resources/prepare/target_per_capita_TFC_{scenario_name}.csv",
        reference_sector_TFC_share=lambda wc: (
            f"resources/processed/IEA_historical_sector_TFC_share_{ref_year}.csv"
        ),
        reference_per_capita_TFC=lambda wc: (
            f"resources/processed/historical_per_capita_TFC_{ref_year}.csv"
        )
    conda:
        "../envs/default.yaml"
    output:
        output_file="resources/prepare/target_sector_TFC_share_{scenario_name}.csv"
    script:
        "../scripts/get_target_sector_TFC_share.py"


rule get_target_elec_rate_by_sector:
    message:
        """
        Prepare for the demand calculation by getting the target electrification rate
        for each sector in each country. 

        Can be specified per country, per sector. If not specified, the default is
        the global value defined in config.
        """
    params:
        countries=config.get("countries", []) or available_countries,
        ref_year=ref_year,
        # country_overwrite="resources/user/country_level_overwrite.csv",
        country_overwrite=lambda wc: "resources/user/country_level_overwrite.csv" if os.path.exists("resources/user/country_level_overwrite.csv") else None,
        sector_overwrite_dir="resources/user/sector_level_overwrite",
        scenario_name=scenario_name,
        sector_elec_rate_rel=config["required"]["sector_elec_rate_rel"],
        elec_rate_in_case_zero=config["required"]["elec_rate_in_case_zero"],
        use_historical=config["required"]["historical_elec_rate"],
    input:
        reference_sector_elec_rate=lambda wc: (
            f"resources/processed/IEA_historical_sector_electrification_{ref_year}.csv"
        )
    output:
        output_file="resources/prepare/target_sector_elec_rate_{scenario_name}.csv"
    conda:
        "../envs/default.yaml"
    script:
        "../scripts/get_target_elec_rate.py"


rule get_target_elec_decarb:
    message:
        """
        Prepare for the demand calculation by getting the target decarbonisation level
        for the electricity part in each sector in each country. 

        Can be specified per country, per sector. If not specified, the default is
        the global value defined in config.
        """
    params:
        countries=config.get("countries", []) or available_countries,
        ref_year=ref_year,
        country_overwrite=lambda wc: "resources/user/country_level_overwrite.csv" if os.path.exists("resources/user/country_level_overwrite.csv") else None,
        sector_overwrite_dir="resources/user/sector_level_overwrite",
        scenario_name=scenario_name,
        elec_decarb_rel=config["required"]["elec_decarb_rel"],
        elec_decarb_in_case_zero=config["required"]["elec_decarb_in_case_zero"],
        use_historical=config["required"]["historical_elec_decarb"],
    input:
        reference_sector_elec_decarb=lambda wc: (
            f"resources/processed/IEA_historical_elec_decarb_{ref_year}.csv"
        )
    output:
        output_file="resources/prepare/target_elec_decarb_{scenario_name}.csv"
    conda:
        "../envs/default.yaml"
    script:
        "../scripts/get_target_elec_decarb.py"


rule get_target_non_elec_decarb:
    message:
        """
        Prepare for the demand calculation by getting the target decarbonisation level
        for the non-electricity part in each sector in each country. 

        Can be specified per country, per sector. If not specified, the default is
        the global value defined in config.
        """
    params:
        countries=config.get("countries", []) or available_countries,
        ref_year=ref_year,
        country_overwrite=lambda wc: "resources/user/country_level_overwrite.csv" if os.path.exists("resources/user/country_level_overwrite.csv") else None,
        sector_overwrite_dir="resources/user/sector_level_overwrite",
        scenario_name=scenario_name,
        non_elec_decarb_rel=config["required"]["non_elec_decarb_rel"],
        non_elec_decarb_in_case_zero=config["required"]["non_elec_decarb_in_case_zero"],
        use_historical=config["required"]["historical_non_elec_decarb"],
    input:
        reference_sector_non_elec_decarb=lambda wc: (
            f"resources/processed/IEA_historical_non_elec_decarb_{ref_year}.csv"
        )
    conda:
        "../envs/default.yaml"
    output:
        output_file="resources/prepare/target_non_elec_decarb_{scenario_name}.csv"
    script:
        "../scripts/get_target_non_elec_decarb.py"


rule calculate_vRES_demand:
    message:
        """
        Calculate electricity demand met by vRES for all considered countries.
        """
    params:
        output_dir="results/demand/",
        country_overwrite=lambda wc: "resources/user/country_level_overwrite.csv" if os.path.exists("resources/user/country_level_overwrite.csv") else None,
    input:
        TFC_per_capita="resources/prepare/target_per_capita_TFC_{scenario_name}.csv",
        sector_TFC_share="resources/prepare/target_sector_TFC_share_{scenario_name}.csv",
        sector_electrification="resources/prepare/target_sector_elec_rate_{scenario_name}.csv",
        sector_elec_decarb="resources/prepare/target_elec_decarb_{scenario_name}.csv",
        elec_loss_rate=lambda wc: (f"resources/processed/IEA_historical_elec_TnD_loss_rate_{ref_year}.csv"),
        other_renewables=lambda wc: (
            f"resources/processed/IEA_historical_other_renewables_prod_{ref_year}.csv"),
        population="resources/processed/population_{population_ref_year}.csv",
    conda:
        "../envs/default.yaml"
    output:
        output_file="results/demand/demand_vRES_{population_ref_year}_{scenario_name}.csv",
    script:
        "../scripts/calculate_demand_vRES.py"


rule calculate_GH2_demand:
    message:
        """
        Calculate green hydrogen demand for all considered countries.
        """
    params:
        output_dir="results/demand/",
        tot_per_capita_TFC=config["required"]["tot_per_capita_TFC"],
        use_historical_per_capita_TFC=config["required"]["historical_per_capita_TFC"],
        country_overwrite=lambda wc: "resources/user/country_level_overwrite.csv" if os.path.exists("resources/user/country_level_overwrite.csv") else None,
        ref_year=ref_year,
    input:
        historical_per_capita_TFC=lambda wc: (
            f"resources/processed/historical_per_capita_TFC_{ref_year}.csv"),
        sector_TFC_share="resources/prepare/target_sector_TFC_share_{scenario_name}.csv",
        sector_electrification="resources/prepare/target_sector_elec_rate_{scenario_name}.csv",
        sector_non_elec_decarb="resources/prepare/target_non_elec_decarb_{scenario_name}.csv",
        population="resources/processed/population_{population_ref_year}.csv",
        hist_non_elec_renew_consum=lambda wc: (f"resources/processed/IEA_historical_non_elec_renew_consum_{ref_year}.csv"),
    conda:
        "../envs/default.yaml"
    output:
        output_file="results/demand/demand_GH2_{population_ref_year}_{scenario_name}.csv",
    script:
        "../scripts/calculate_demand_GH2.py"