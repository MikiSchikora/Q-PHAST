# A python3 script to run the pipeline from any OS

############# ENV ############

# imports
import os, sys, argparse, shutil, subprocess
from pathlib import Path

description = """
This is a pipeline to measure antifungal susceptibility from image data in any OS. Run with: 

    In linux and mac: 'python3 main.py <arguments>'

    In windows: 'py main.py <arguments>'

Check the github repository (https://github.comGabaldonlab/qCAST) to know how to use this script.
"""

# mandatory arguments              
parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--os", dest="os", required=True, type=str, help="The Operating System. It should be 'windows', 'linux' or 'mac'")
parser.add_argument("--module", dest="module", required=True, type=str, help="The module to run. It may be 'get_plate_layout' or 'analyze_images'")
parser.add_argument("--output", dest="output", required=True, type=str, help="The output directory.")
parser.add_argument("--docker_image", dest="docker_image", required=True, type=str, help="The name of the docker image in the format <name>:<tag>. All the versions of the images are in https://hub.docker.com/repository/docker/mikischikora/qcast. For example, you can set '--docker_image mikischikora/qcast:v1' to run version 1.")

# optional args for each module
parser.add_argument("--strains", dest="strains", required=False, default=None, type=str, help="An excel table with the list of strains. This only has an effect if --module is 'get_plate_layout'")
parser.add_argument("--drugs", dest="drugs", required=False, default=None, type=str, help="An excel table with the list of drugs and concentrations. This only has an effect if --module is 'get_plate_layout'")
parser.add_argument("--plate_layout", dest="plate_layout", required=False, default=None, type=str, help="An excel table with the plate layout in long format. This should be the file 'plate_layout_long'.xlsx genertaed by the 'get_plate_layout' module. This only has an effect if --module is 'analyze_images'")
parser.add_argument("--images", dest="images", required=False, default=None, type=str, help="A folder with the raw images to analyze. It should contain one subfolder (named after the plate batch) with the images of each 'plate_batch'. This only has an effect if --module is 'analyze_images'")
parser.add_argument("--keep_tmp_files", dest="keep_tmp_files", required=False, default=False, action="store_true", help="Keep the intermediate files (for debugging).")
parser.add_argument("--replace", dest="replace", required=False, default=False, action="store_true", help="Remove the --output folder to repeat any previously run processes.")

parser.add_argument("--pseudocount_log2_concentration", dest="pseudocount_log2_concentration", required=False, type=float, default=0.1, help="A float that is used to pseudocount the concentrations for susceptibility measures. This only has an effect if --module is 'analyze_images'")
parser.add_argument("--min_nAUC_to_beConsideredGrowing", dest="min_nAUC_to_beConsideredGrowing", required=False, type=float, default=0.5, help="A float that indicates the minimum nAUC to be considered growing in susceptibility measures. This may depend on the experiment. This is added in the 'is_growing' field. This only has an effect if --module is 'analyze_images'")
parser.add_argument("--min_points_to_calculate_resistance_auc", dest="min_points_to_calculate_resistance_auc", required=False, type=int, default=4, help="An integer number indicating the minimum number of points required to calculate the rAUC for susceptibility measures. This only has an effect if --module is 'analyze_images'")

# parse
opt = parser.parse_args()

##############################

##### DEFINE FUNCTIONS #######

def get_fullpath(x):

    """Takes a path and substitutes it bu the full path"""

    if opt.os in {"linux", "mac"}:
        if x.startswith("/"): return x

        # a ./    
        elif x.startswith("./"): return "%s/%s"%(os.getcwd(), "/".join(x.split("/")[1:]))

        # others (including ../)
        else: return "%s/%s"%(os.getcwd(), x)

    elif opt.os=="windows":
        if Path(x).is_absolute() is True: return x

        # a .\
        elif x.startswith(".\\"): return "%s\\%s"%(os.getcwd(), "\\".join(x.split("\\")[1:]))

        # others (including ..\)
        else: return "%s\\%s"%(os.getcwd(), x)

    else: raise ValueError("--os should have 'linux', 'mac' or 'windows'")

def run_cmd(cmd):

    """Runs os.system in cmd"""

    out_stat = os.system(cmd) 
    if out_stat!=0: raise ValueError("\n%s\n did not finish correctly. Out status: %i"%(cmd, out_stat))

def make_folder(f):

    if not os.path.isdir(f): os.mkdir(f)


def remove_file(f):

    if os.path.isfile(f): os.unlink(f)

def delete_folder(f):

    if os.path.isdir(f): shutil.rmtree(f)

def file_is_empty(path): 
    
    """ask if a file is empty or does not exist """

    if not os.path.isfile(path): return True
    elif os.stat(path).st_size==0: return True
    else: return False

def get_os_sep(): return {"windows":"\\", "linux":"/", "mac":"/"}[opt.os]

def copy_file(origin_file, dest_file):

    """Copies file"""

    dest_file_tmp = "%s.tmp"%dest_file
    shutil.copy(origin_file, dest_file_tmp)
    os.rename(dest_file_tmp, dest_file)

##############################

######  DEBUG INPUTS #########

# replace
if opt.replace is True: delete_folder(opt.output)

# arguments of each module
if opt.module=="get_plate_layout":
    if opt.strains is None or opt.drugs is None: raise ValueError("For module get_plate_layout, you should provide the --strains and --drugs arguments.")
    opt.strains = get_fullpath(opt.strains)
    opt.drugs = get_fullpath(opt.drugs)
    if file_is_empty(opt.strains): raise ValueError("The file provided in --strains does not exist or it is empty")
    if file_is_empty(opt.drugs): raise ValueError("The file provided in --drugs does not exist or it is empty")

elif opt.module=="analyze_images":
    if opt.plate_layout is None or opt.images is None: raise ValueError("For module analyze_images, you should provide the --plate_layout and --images arguments.")
    opt.plate_layout = get_fullpath(opt.plate_layout)
    opt.images = get_fullpath(opt.images)
    if file_is_empty(opt.plate_layout): raise ValueError("The file provided in --plate_layout does not exist or it is empty")
    if not os.path.isdir(opt.images): raise ValueError("The folder provided in --images does not exist")

else: raise ValueError("--module should have 'get_plate_layout' or 'analyze_images'")

# check the OS
if not opt.os in {"linux", "mac", "windows"}: raise ValueError("--os should have 'linux', 'mac' or 'windows'")

# check that the docker image can be run
print("Trying to run docker image. If this fails it may be because either the image is not in your system or docker is not properly initialized.")
run_cmd('docker run -it --rm %s bash -c "sleep 1"'%(opt.docker_image))

#############################

######### GENERATE THE DOCKER CMD AND RUN #################

# make the output
opt.output = get_fullpath(opt.output)
make_folder(opt.output)

# make the inputs_dir, where the small inputs will be stored
tmp_input_dir = "%s%stmp_small_inputs"%(opt.output, get_os_sep())
delete_folder(tmp_input_dir); make_folder(tmp_input_dir)

# init command with general features
docker_cmd = 'docker run --rm -it -e MODULE=%s -e KEEP_TMP_FILES=%s -e pseudocount_log2_concentration=%s -e min_nAUC_to_beConsideredGrowing=%s -e min_points_to_calculate_resistance_auc=%s -v "%s":/small_inputs -v "%s":/output'%(opt.module, opt.keep_tmp_files, opt.pseudocount_log2_concentration, opt.min_nAUC_to_beConsideredGrowing, opt.min_points_to_calculate_resistance_auc, tmp_input_dir, opt.output)

# add the scripts from outside (debug)
if opt.os in {"linux", "mac"}: CurDir = get_fullpath("/".join(__file__.split("/")[0:-1]))
elif opt.os=="windows": CurDir = get_fullpath("\\".join(__file__.split("\\")[0:-1]))
docker_cmd += ' -v "%s%sscripts":/workdir_app/scripts'%(CurDir, get_os_sep())

# configure for each os
if opt.os=="linux":

    docker_cmd = 'xhost +local:docker && %s'%docker_cmd
    docker_cmd += ' -e DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix'

elif opt.os=="mac":

    local_IP = str(subprocess.check_output("ifconfig en0 | grep 'inet '", shell=True)).split("inet")[1].split()[0]
    docker_cmd = 'xhost +%s && %s'%(local_IP, docker_cmd)
    docker_cmd += ' -e DISPLAY=%s:0'%local_IP

elif opt.os=="windows":

    docker_cmd += " -e DISPLAY=host.docker.internal:0.0"

# copy files and update the docker_cmd for each module
if opt.module=="get_plate_layout":
    copy_file(opt.strains, "%s%sstrains.xlsx"%(tmp_input_dir, get_os_sep()))
    copy_file(opt.drugs, "%s%sdrugs.xlsx"%(tmp_input_dir, get_os_sep()))

elif opt.module=="analyze_images":
    copy_file(opt.plate_layout, "%s%splate_layout_long.xlsx"%(tmp_input_dir, get_os_sep()))
    docker_cmd += ' -v "%s":/images'%opt.images

# at the end add the name of the image
docker_stderr = "%s%sdocker_stderr.txt"%(opt.output, get_os_sep())
docker_cmd += ' %s bash -c "source /opt/conda/etc/profile.d/conda.sh && conda activate main_env > /dev/null 2>&1 && /workdir_app/scripts/run_app.py 2>/output/docker_stderr.txt"'%(opt.docker_image)

# run
print("Running docker image with the following cmd:\n---\n%s\n---\n"%docker_cmd)

try: run_cmd(docker_cmd)
except: 
    print("\n\nERROR: The run of the pipeline failed. This is the error log:\n---\n%s\n---\nExiting with code 1!"%("".join(open(docker_stderr, "r").readlines())))
    sys.exit(1)

# clean
remove_file(docker_stderr)
delete_folder(tmp_input_dir) # clean
print("main.py %s worked successfully!"%opt.module)

###########################################################

