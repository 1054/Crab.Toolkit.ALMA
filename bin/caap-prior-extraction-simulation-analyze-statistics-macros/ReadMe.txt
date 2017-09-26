This is a bunch of code for 'caap-prior-extraction-simulation'

The simulation is done for ALMA image data. 

The output of the simulation and recovery (prior extraction photometry) should yield the following files: 
    'datatable_Simulated.txt'
    'datatable_Recovered_galfit.txt'
    'info_synthesized_beam.txt' (one or two columns, one row)
    'info_primary_beam.txt' (one column, one row)

Then we can run these supermongo macros, but make sure you have 'https://github.com/1054/DeepFields.SuperDeblending/' cloned and 
    bash
    source /path/to/DeepFields.SuperDeblending/Softwares/SETUP
    echo "macro read a_dzliu_code_compile_simu_data.sm go" | sm
    #--> outputs are '*.pdf', 'simu_data_input.txt'
    echo "macro read a_dzliu_code_run_simu_stats.sm analyze_statistics" | sm
    #--> outputs are 'sim_diagram_output_v11/*'


