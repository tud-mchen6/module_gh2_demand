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

scenario_name = config["scenario"]
scenario_config = config["scenarios"][scenario_name]
ref_year = scenario_config.get("year_for_IEA_balance", 2023)
population_ref_year = scenario_config["population_ref_year"]
population_scenario = scenario_config["population_scenario"]


rule get_target_TFC_per_capita:
    message:
        """
        Prepare for the demand calculation by getting the target total final consumption
        per capita for each country.
        """
    params:
        countries=available_countries,
        scenario_name=scenario_name,
        use_historical=scenario_config["historical_per_capita_TFC"],
        tot_per_capita_TFC=scenario_config["tot_per_capita_TFC"],
    input:
        # TODO: in the integrated workflow, this file needs to be manually put there - write in README
        country_overwrite="<resources>/user/country_level_overwrite.csv",
        reference_per_capita_TFC=lambda wc: (
            f"<resources>/processed/IEA_historical_per_capita_TFC_{ref_year}.csv"
        )
    conda:
        "../envs/default.yaml"
    output:
        output_file="<resources>/prepare/target_per_capita_TFC_{scenario_name}.csv"
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
        ref_year=ref_year,
        sector_overwrite_dir="<resources>/user/sector_level_overwrite",
        scenario_name=scenario_name,
    input:
        country_overwrite="<resources>/user/country_level_overwrite.csv",
        TFC_per_capita="<resources>/prepare/target_per_capita_TFC_{scenario_name}.csv",
        reference_sector_TFC_share=lambda wc: (
            f"<resources>/processed/IEA_historical_sector_TFC_share_{ref_year}.csv"
        ),
        reference_per_capita_TFC=lambda wc: (
            f"<resources>/processed/IEA_historical_per_capita_TFC_{ref_year}.csv"
        )
    conda:
        "../envs/default.yaml"
    output:
        output_file="<resources>/prepare/target_sector_TFC_share_{scenario_name}.csv"
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
        ref_year=ref_year,
        sector_overwrite_dir="<resources>/user/sector_level_overwrite",
        scenario_name=scenario_name,
        sector_elec_rate_rel=scenario_config["sector_elec_rate_rel"],
        elec_rate_in_case_zero=scenario_config["elec_rate_in_case_zero"],
        use_historical=scenario_config["historical_elec_rate"],
    input:
        country_overwrite="<resources>/user/country_level_overwrite.csv",
        reference_sector_elec_rate=lambda wc: (
            f"<resources>/processed/IEA_historical_sector_electrification_{ref_year}.csv"
        )
    output:
        output_file="<resources>/prepare/target_sector_elec_rate_{scenario_name}.csv"
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
        ref_year=ref_year,
        sector_overwrite_dir="<resources>/user/sector_level_overwrite",
        scenario_name=scenario_name,
        elec_decarb_rel=scenario_config["elec_decarb_rel"],
        elec_decarb_in_case_zero=scenario_config["elec_decarb_in_case_zero"],
        use_historical=scenario_config["historical_elec_decarb"],
    input:
        country_overwrite="<resources>/user/country_level_overwrite.csv",
        reference_sector_elec_decarb=lambda wc: (
            f"<resources>/processed/IEA_historical_elec_decarb_{ref_year}.csv"
        )
    output:
        output_file="<resources>/prepare/target_elec_decarb_{scenario_name}.csv"
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
        ref_year=ref_year,
        sector_overwrite_dir="<resources>/user/sector_level_overwrite",
        scenario_name=scenario_name,
        non_elec_decarb_rel=scenario_config["non_elec_decarb_rel"],
        non_elec_decarb_in_case_zero=scenario_config["non_elec_decarb_in_case_zero"],
        use_historical=scenario_config["historical_non_elec_decarb"],
    input:
        country_overwrite="<resources>/user/country_level_overwrite.csv",
        reference_sector_non_elec_decarb=lambda wc: (
            f"<resources>/processed/IEA_historical_non_elec_decarb_{ref_year}.csv"
        )
    conda:
        "../envs/default.yaml"
    output:
        output_file="<resources>/prepare/target_non_elec_decarb_{scenario_name}.csv"
    script:
        "../scripts/get_target_non_elec_decarb.py"


rule calculate_vRES_demand:
    message:
        """
        Calculate electricity demand met by vRES for all considered countries.
        """
    input:
        TFC_per_capita=f"<resources>/prepare/target_per_capita_TFC_{scenario_name}.csv",
        sector_TFC_share=f"<resources>/prepare/target_sector_TFC_share_{scenario_name}.csv",
        sector_electrification=f"<resources>/prepare/target_sector_elec_rate_{scenario_name}.csv",
        sector_elec_decarb=f"<resources>/prepare/target_elec_decarb_{scenario_name}.csv",
        elec_loss_rate=f"<resources>/processed/IEA_historical_elec_TnD_loss_rate_{ref_year}.csv",
        other_renewables=f"<resources>/processed/IEA_historical_other_renewables_prod_{ref_year}.csv",
        population=f"<resources>/processed/population_{population_scenario}_{population_ref_year}.csv",
    output:
        output_file=f"<results>/demand/demand_vRES_{scenario_name}.csv",
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
        TFC_per_capita=f"<resources>/prepare/target_per_capita_TFC_{scenario_name}.csv",
        sector_TFC_share=f"<resources>/prepare/target_sector_TFC_share_{scenario_name}.csv",
        sector_electrification=f"<resources>/prepare/target_sector_elec_rate_{scenario_name}.csv",
        sector_non_elec_decarb=f"<resources>/prepare/target_non_elec_decarb_{scenario_name}.csv",
        population=f"<resources>/processed/population_{population_scenario}_{population_ref_year}.csv",
        hist_non_elec_renew_consum=f"<resources>/processed/IEA_historical_non_elec_renew_consum_{ref_year}.csv",
    conda:
        "../envs/default.yaml"
    output:
        output_file=f"<results>/demand/demand_GH2_{scenario_name}.csv",
    script:
        "../scripts/calculate_demand_GH2.py"