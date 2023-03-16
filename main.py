# A python3 script to run the pipeline from any OS

############# ENV ############

# imports
import os, sys, argparse, subprocess, re, time

# general functions

# add the functions
if "/" in os.getcwd(): os_sep = "/"
elif "\\" in os.getcwd(): os_sep = "\\"
else: raise ValueError("unknown OS. This script is %s"%__file__)

pipeline_dir = os_sep.join(os.path.realpath(__file__).split(os_sep)[0:-1])
sys.path.insert(0, '%s%sscripts'%(pipeline_dir, os_sep))
import main_functions as fun

description = """
This is a pipeline to measure antifungal susceptibility from image data in any OS. Run with: 

    In linux and mac: 'python3 main.py <arguments>'

    In windows: 'py main.py <arguments>'

Check the github repository (https://github.comGabaldonlab/Q-PHAST) to know how to use this script.
"""

# mandatory arguments (if run in command line)               
parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--os", dest="os", required=False, default=None, type=str, help="The Operating System. It should be 'windows', 'linux' or 'mac'")
parser.add_argument("--output", dest="output", required=False, default=None, type=str, help="The output directory.")
parser.add_argument("--docker_image", dest="docker_image", required=False, default=None, type=str, help="The name of the docker image in the format <name>:<tag>. All the versions of the images are in https://hub.docker.com/repository/docker/mikischikora/q-phast. For example, you can set '--docker_image mikischikora/q-phast:v1' to run version 1.")
parser.add_argument("--input", dest="input", required=False, default=None, type=str, help="A folder with the plate layout and the raw images to analyze. It should contain one subfolder (named after the plate batch) with the images of each 'plate_batch'.")

# optional arguments
parser.add_argument("--keep_tmp_files", dest="keep_tmp_files", required=False, default=False, action="store_true", help="Keep the intermediate files (forqca debugging).")
parser.add_argument("--replace", dest="replace", required=False, default=False, action="store_true", help="Remove the --output folder to repeat any previously run processes.")
parser.add_argument("--pseudocount_log2_concentration", dest="pseudocount_log2_concentration", required=False, type=float, default=0.1, help="A float that is used to pseudocount the concentrations for susceptibility measures.")
parser.add_argument("--min_nAUC_to_beConsideredGrowing", dest="min_nAUC_to_beConsideredGrowing", required=False, type=float, default=0.5, help="A float that indicates the minimum nAUC to be considered growing in susceptibility measures. This may depend on the experiment. This is added in the 'is_growing' field.")
parser.add_argument("--min_points_to_calculate_resistance_auc", dest="min_points_to_calculate_resistance_auc", required=False, type=int, default=4, help="An integer number indicating the minimum number of points required to calculate the rAUC for susceptibility measures.")


# developer args
parser.add_argument("--skip_contrast_correction", dest="skip_contrast_correction", required=False, default=False, action="store_true", help="Skips the contrast correction of images.")
parser.add_argument("--break_after", dest="break_after", required=False, type=str, default=None, help="Break after some steps")

# parse
opt = parser.parse_args()

# pass the opt to functions
fun.opt = opt

# log
print("\n")
fun.print_with_runtime("Running Q-PHAST...")

##############################

##### RUN GUI TO DEFINE ARGUMENTS #########

# only get arguments through GUI if there are no arguments passed
if len(sys.argv)==1:

    # generate a series of buttons that select common arguments
    fun.generate_os_window()
    fun.generate_docker_image_window()

    # generate the window of each type of args
    fun.generate_analyze_images_window_mandatory()

    # define the replace window
    fun.generate_replace_window()

    # define the output and input
    opt.output = "%s%soutput_%s"%(opt.output, fun.get_os_sep(), fun.pipeline_name)

    # generate the image analysis
    fun.generate_analyze_images_window_optional()

    # generate the closing window
    fun.generate_closing_window("Running %s..."%fun.pipeline_name)

    # log
    #print("Running pipeline...")

###########################################

# keep start time
start_time = time.time()

######  DEBUG INPUTS #########

# check that the mandatory args are not none
if opt.docker_image is None: raise ValueError("You should provide a string in --docker_image")
if opt.input is None: raise ValueError("You should provide a string in --input")
if opt.output is None: raise ValueError("You should provide a string in --output")

opt.input = fun.get_fullpath(opt.input)
opt.output = fun.get_fullpath(opt.output)
if not os.path.isdir(opt.input): raise ValueError("The folder provided in --input does not exist")

# replace
if opt.replace is True: fun.delete_folder(opt.output)

# check the OS
if not opt.os in {"linux", "mac", "windows"}: raise ValueError("--os should have 'linux', 'mac' or 'windows'")

# log
fun.print_with_runtime("Writing results into the output folder '%s', using input files from '%s'"%(opt.output, opt.input))

# print the cmd
arguments = " ".join(["--%s %s"%(arg_name, arg_val) for arg_name, arg_val in [("os", opt.os), ("input", opt.input), ("output", opt.output), ("docker_image", opt.docker_image), ("pseudocount_log2_concentration", opt.pseudocount_log2_concentration), ("min_nAUC_to_beConsideredGrowing", opt.min_nAUC_to_beConsideredGrowing), ("min_points_to_calculate_resistance_auc", opt.min_points_to_calculate_resistance_auc)]])

if opt.keep_tmp_files is True: arguments += " --keep_tmp_files"
if opt.replace is True: arguments += " --replace"

full_command = "%s %s%smain.py %s"%(sys.executable, pipeline_dir, os_sep, arguments)
fun.print_with_runtime("Executing the following command (you may use it to reproduce the analysis):\n---\n%s\n---"%full_command)

# check that the docker image can be run
fun.print_with_runtime("Trying to run docker image. If this fails it may be because either the image is not in your system or docker is not properly initialized.")
fun.run_cmd('docker run -it --rm %s bash -c "sleep 1"'%(opt.docker_image))

#############################

######### GENERATE THE DOCKER CMD AND RUN #################

# define the plate layout file
plate_layout_file = "%s%s%s"%(opt.input, fun.get_os_sep(), fun.get_plate_layout_file_from_input_dir(opt.input))

# make the output
opt.output = fun.get_fullpath(opt.output)
fun.make_folder(opt.output)

# define the inputs_dir, where the small inputs will be stored
tmp_input_dir = "%s%stmp_small_inputs"%(opt.output, fun.get_os_sep())
copied_plate_layout = "%s%splate_layout.xlsx"%(tmp_input_dir, fun.get_os_sep())

# if there was a previous run (copied_plate_layout exists), replace everything if the plate layout changed
if not fun.file_is_empty(copied_plate_layout) and not fun.get_if_excels_are_equal(plate_layout_file, copied_plate_layout):

    fun.print_with_runtime("WARNING: You are providing a different plate layout than in a previous run\n")
    fun.backwards_timer_print_text(15, 'WARNING: Thus, deleting previously-generated files in <output> in ')
    fun.delete_folder(opt.output)
    fun.print_with_runtime("WARNING: Previously-generated files in <output> deleted.")

# make the input dir
fun.make_folder(opt.output)
fun.delete_folder(tmp_input_dir); fun.make_folder(tmp_input_dir)

# init command with general features
docker_cmd = 'docker run --rm -it -e KEEP_TMP_FILES=%s -e pseudocount_log2_concentration=%s -e min_nAUC_to_beConsideredGrowing=%s -e min_points_to_calculate_resistance_auc=%s -e skip_contrast_correction=%s -v "%s":/small_inputs -v "%s":/output -v "%s":/images'%(opt.keep_tmp_files, opt.pseudocount_log2_concentration, opt.min_nAUC_to_beConsideredGrowing, opt.min_points_to_calculate_resistance_auc, opt.skip_contrast_correction, tmp_input_dir, opt.output, opt.input)

# add the scripts from outside
docker_cmd += ' -v "%s%sscripts":/workdir_app/scripts'%(pipeline_dir, fun.get_os_sep())

# pass the plate layout to docker
fun.copy_file(plate_layout_file, copied_plate_layout)

# get the corrected images
print("\n")
fun.print_with_runtime("STEP 1/5: Getting cropped, flipped images with improved contrast...")
fun.run_docker_cmd("%s -e MODULE=analyze_images_process_images"%(docker_cmd), ["%s%sanalyze_images_process_images_correct_finish.txt"%(opt.output, fun.get_os_sep())])

if opt.break_after=="step1": 
    print("Exiting pipeline after step 1...")
    sys.exit(0)

# select the coordinates based on user input
print("\n")
fun.print_with_runtime("STEP 2/5: Selecting the coordinates of the spots...")
fun.get_colonyzer_coordinates_GUI(opt.output, docker_cmd)

# get fitness measurements
print("\n")
fun.print_with_runtime("STEP 3/5: Getting fitness measurements...")
fun.run_docker_cmd("%s -e MODULE=get_fitness_measurements"%(docker_cmd), ["%s%sget_fitness_measurements_correct_finish.txt"%(opt.output, fun.get_os_sep())])

# validate bad spots
print("\n")
fun.print_with_runtime("STEP 4/5: Manually-curating bad spots...")
fun.generate_df_bad_spots_automatic_validated(opt.output)

if opt.break_after=="step4": 
    print("Exiting pipeline after step 4...")
    sys.exit(0)

# Get the relative fitness and susceptibility measurements
print("\n")
fun.print_with_runtime("STEP 5/5: Getting integrated fitness and susceptibility measurements...")
fun.run_docker_cmd("%s -e MODULE=get_rel_fitness_and_susceptibility_measurements"%(docker_cmd), ["%s%sget_rel_fitness_and_susceptibility_measurements_correct_finish.txt"%(opt.output, fun.get_os_sep())])

# clean
for f in ['analyze_images_run_colonyzer_subset_images_correct_finish.txt', 'analyze_images_process_images_correct_finish.txt', 'get_fitness_measurements_correct_finish.txt', 'get_rel_fitness_and_susceptibility_measurements_correct_finish.txt']: fun.remove_file("%s%s%s"%(opt.output, fun.get_os_sep(), f))
fun.delete_folder(tmp_input_dir)
#fun.delete_folder("%s%sextended_outputs%sreduced_input_dir.zip"%(opt.output, fun.get_os_sep(), fun.get_os_sep()))

# log
fun.print_with_runtime("main.py worked successfully in %.2f seconds!"%(time.time()-start_time))

###########################################################

