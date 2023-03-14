# This is a python script to test that all the subsets testing work

# imports
import os, sys, platform

# define the os_sep
if "/" in os.getcwd(): os_sep = "/"
elif "\\" in os.getcwd(): os_sep = "\\"
else: raise ValueError("unknown OS. This script is %s"%__file__)

# define the current directory
CurDir = os_sep.join(os.path.realpath(__file__).split(os_sep)[0:-1])

# import main functions
sys.path.insert(0, '%s%s..%s..%sscripts'%(CurDir, os_sep, os_sep, os_sep))
import main_functions as fun

# test each of the samples that should work
for d in ["AST_48h_subset", "Classic_spottest_subset", "Fitness_only_subset", "Stress_plates_subset"]:
#for d in ["Classic_spottest_subset"]:

    print("testing %s..."%d)

    # define the testdir
    test_dir = "%s%s%s"%(CurDir, os_sep, d)
    input_dir = "%s%sinput"%(test_dir, os_sep)
    output_dir = "%s%soutput_Q-PHAST"%(test_dir, os_sep)
    #fun.delete_folder(output_dir)

    running_os = {"Darwin":"mac", "Linux":"linux", "Windows":"windows"}[platform.system()]

    # run the python script
    main_script = '%s%s..%s..%smain.py'%(CurDir, os_sep, os_sep, os_sep)
    fun.run_cmd("python %s --os %s --input %s --docker_image mikischikora/q-phast:v1 --output %s --pseudocount_log2_concentration 0.1 --min_nAUC_to_beConsideredGrowing 0.5 --min_points_to_calculate_resistance_auc 4 --keep_tmp_files"%(main_script, running_os, input_dir, output_dir))










# test that the errors generated by different plate layouts from Stress_plates_subset are meaningful



#output
#testing/testing_subsets/Stress_plates_subset/testing_different_platelayouts 

"""
Dockerignore content:

testing/testing_subsets/AST_48h_subset/output_Q-PHAST
testing/testing_subsets/Classic_spottest_subset/output_Q-PHAST
testing/testing_subsets/Fitness_only_subset/output_Q-PHAST
testing/testing_subsets/Stress_plates_subset/output_Q-PHAST
testing/testing_subsets/Stress_plates_subset/testing_different_platelayouts
"""