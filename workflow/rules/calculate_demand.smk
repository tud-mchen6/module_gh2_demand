"""Rules to use user-provided parameters and in case of need, 
historical data to produce top-down electricity demand met by
variable renewable energy sources and green hydrogen."""

import glob
import os

configfile: "config/config.yaml"

# Get all available CSVs automatically
available_countries = [
    os.path.basename(f).split("_")[2]   # hard-coded, the part after the prefix
    for f in glob.glob("<resources>/automatic/IEA_energy_balances/IEA_EnergyBalance_*.csv")
]

def get_scenario_config(wildcards):
    return config["scenarios"][wildcards.scenario]
def get_year(wildcards):
    return get_scenario_config(wildcards).get(
        "year_for_IEA_balance", 2023
    )
def get_population_scenario(wildcards):
    return get_scenario_config(wildcards)["population_scenario"]
def get_population_ref_year(wildcards):
    return get_scenario_config(wildcards)["population_ref_year"]
def get_historical_per_capita_TFC(wildcards):
    return get_scenario_config(wildcards)["historical_per_capita_TFC"]
def get_tot_per_capita_TFC(wildcards):
    return get_scenario_config(wildcards)["tot_per_capita_TFC"]
def get_sector_elec_rate_rel(wildcards):
    return get_scenario_config(wildcards)["sector_elec_rate_rel"]
def get_elec_rate_in_case_zero(wildcards):
    return get_scenario_config(wildcards)["elec_rate_in_case_zero"]
def get_historical_elec_rate(wildcards):
    return get_scenario_config(wildcards)["historical_elec_rate"]
def get_historical_elec_decarb(wildcards):
    return get_scenario_config(wildcards)["historical_elec_decarb"]
def get_elec_decarb_rel(wildcards):
    return get_scenario_config(wildcards)["elec_decarb_rel"]
def get_elec_decarb_in_case_zero(wildcards):
    return get_scenario_config(wildcards)["elec_decarb_in_case_zero"]
def get_non_elec_decarb_rel(wildcards):
    return get_scenario_config(wildcards)["non_elec_decarb_rel"]
def get_non_elec_decarb_in_case_zero(wildcards):
    return get_scenario_config(wildcards)["non_elec_decarb_in_case_zero"]
def get_historical_non_elec_decarb(wildcards):
    return get_scenario_config(wildcards)["historical_non_elec_decarb"]


rule get_target_TFC_per_capita:
    message:
        """
        Prepare for the demand calculation by getting the target total final consumption
        per capita for each country.
        """
    params:
        countries=available_countries,
        use_historical=get_historical_per_capita_TFC,
        tot_per_capita_TFC=get_tot_per_capita_TFC,
    input:
        # TODO: in the integrated workflow, this file needs to be manually put there - write in README
        country_overwrite="<resources>/user/country_level_overwrite.csv",
        reference_per_capita_TFC=lambda wc: (
            f"<resources>/processed/IEA_historical_per_capita_TFC_{get_year(wc)}.csv"
        )
    conda:
        "../envs/default.yaml"
    output:
        output_file="<resources>/prepare/target_per_capita_TFC_{scenario}.csv"
    script:
        "../scripts/get_target_TFC_per_capita.py"


rule get_target_sector_TFC_share:
    message:
        """
        Prepare for the demand calculation by getting the target sector share in the
        total final consumption for each country.
        """
    params:
        countries=available_countries,
        ref_year=get_population_ref_year,
        sector_overwrite_dir="<resources>/user/sector_level_overwrite",
    input:
        country_overwrite="<resources>/user/country_level_overwrite.csv",
        TFC_per_capita="<resources>/prepare/target_per_capita_TFC_{scenario}.csv",
        reference_sector_TFC_share=lambda wc: (
            f"<resources>/processed/IEA_historical_sector_TFC_share_{get_year(wc)}.csv"
        ),
        reference_per_capita_TFC=lambda wc: (
            f"<resources>/processed/IEA_historical_per_capita_TFC_{get_year(wc)}.csv"
        )
    conda:
        "../envs/default.yaml"
    output:
        output_file="<resources>/prepare/target_sector_TFC_share_{scenario}.csv"
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
        countries=available_countries,
        ref_year=get_population_ref_year,
        sector_overwrite_dir="<resources>/user/sector_level_overwrite",
        sector_elec_rate_rel=get_sector_elec_rate_rel,
        elec_rate_in_case_zero=get_elec_rate_in_case_zero,
        use_historical=get_historical_elec_rate,
    input:
        country_overwrite="<resources>/user/country_level_overwrite.csv",
        reference_sector_elec_rate=lambda wc: (
            f"<resources>/processed/IEA_historical_sector_electrification_{get_year(wc)}.csv"
        )
    output:
        output_file="<resources>/prepare/target_sector_elec_rate_{scenario}.csv"
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
        countries=available_countries,
        ref_year=get_population_ref_year,
        sector_overwrite_dir="<resources>/user/sector_level_overwrite",
        elec_decarb_rel=get_elec_decarb_rel,
        elec_decarb_in_case_zero=get_elec_decarb_in_case_zero,
        use_historical=get_historical_elec_decarb,
    input:
        country_overwrite="<resources>/user/country_level_overwrite.csv",
        reference_sector_elec_decarb=lambda wc: (
            f"<resources>/processed/IEA_historical_elec_decarb_{get_year(wc)}.csv"
        )
    output:
        output_file="<resources>/prepare/target_elec_decarb_{scenario}.csv"
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
        countries=available_countries,
        ref_year=get_population_ref_year,
        sector_overwrite_dir="<resources>/user/sector_level_overwrite",
        non_elec_decarb_rel=get_non_elec_decarb_rel,
        non_elec_decarb_in_case_zero=get_non_elec_decarb_in_case_zero,
        use_historical=get_historical_non_elec_decarb,
    input:
        country_overwrite="<resources>/user/country_level_overwrite.csv",
        reference_sector_non_elec_decarb=lambda wc: (
            f"<resources>/processed/IEA_historical_non_elec_decarb_{get_year(wc)}.csv"
        )
    conda:
        "../envs/default.yaml"
    output:
        output_file="<resources>/prepare/target_non_elec_decarb_{scenario}.csv"
    script:
        "../scripts/get_target_non_elec_decarb.py"


rule calculate_vRES_demand:
    message:
        """
        Calculate electricity demand met by vRES for all considered countries.
        """
    input:
        TFC_per_capita="<resources>/prepare/target_per_capita_TFC_{scenario}.csv",
        sector_TFC_share="<resources>/prepare/target_sector_TFC_share_{scenario}.csv",
        sector_electrification="<resources>/prepare/target_sector_elec_rate_{scenario}.csv",
        sector_elec_decarb="<resources>/prepare/target_elec_decarb_{scenario}.csv",
        elec_loss_rate=lambda wc: (f"<resources>/processed/IEA_historical_elec_TnD_loss_rate_{get_year(wc)}.csv"),
        other_renewables=lambda wc: (f"<resources>/processed/IEA_historical_other_renewables_prod_{get_year(wc)}.csv"),
        population=lambda wc: (f"<resources>/processed/population_{get_population_scenario(wc)}_{get_population_ref_year(wc)}.csv"),
    output:
        output_file="<results>/demand/demand_vRES_{scenario}.csv",
    conda:
        "../envs/default.yaml"
    script:
        "../scripts/calculate_demand_vRES.py"


rule calculate_GH2_demand:
    message:
        """
        Calculate green hydrogen demand for all considered countries.
        """
    input:
        TFC_per_capita="<resources>/prepare/target_per_capita_TFC_{scenario}.csv",
        sector_TFC_share="<resources>/prepare/target_sector_TFC_share_{scenario}.csv",
        sector_electrification="<resources>/prepare/target_sector_elec_rate_{scenario}.csv",
        sector_non_elec_decarb="<resources>/prepare/target_non_elec_decarb_{scenario}.csv",
        population=lambda wc: (f"<resources>/processed/population_{get_population_scenario(wc)}_{get_population_ref_year(wc)}.csv"),
        hist_non_elec_renew_consum=lambda wc: (f"<resources>/processed/IEA_historical_non_elec_renew_consum_{get_year(wc)}.csv"),
    conda:
        "../envs/default.yaml"
    output:
        output_file="<results>/demand/demand_GH2_{scenario}.csv",
    script:
        "../scripts/calculate_demand_GH2.py"