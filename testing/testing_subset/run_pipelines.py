# This script is to run the pipelines on different systems with python in our systems

# env
import os, subprocess, sys, shutil

# log
print("testing pipelines...")

# define the OS
if os.system("ls > /dev/null 2>&1")==0:
	uname_std = str(subprocess.check_output("uname", shell=True)).split("'")[1].split("\\n")[0]
	if uname_std=="Linux": operating_system = "linux"
	elif uname_std=="Darwin": operating_system = "mac"
	else: raise ValueError("invalid %s"%uname_std)

else: operating_system = "windows"	
print("running in %s"%operating_system)

# define functions
def run_cmd(cmd):

    out_stat = os.system(cmd) 
    if out_stat!=0: raise ValueError("\n%s\n did not finish correctly. Out status: %i"%(cmd, out_stat))

def make_folder(f):
    if not os.path.isdir(f): os.mkdir(f)

def delete_folder(f):
    if os.path.isdir(f): shutil.rmtree(f)

def file_is_empty(path): 
    if not os.path.isfile(path): return True
    elif os.stat(path).st_size==0: return True
    else: return False

# define the sep
sep = {"linux":"/", "mac":"/", "windows":"\\"}[operating_system]
python_exec = {"linux":"python3", "mac":"python3", "windows":"py"}[operating_system]

# define the dirs
qCAST_dir = sep.join(os.getcwd().split(sep)[0:-2])

# define the curdir
if operating_system=="windows":

	# copy files to targe
	C_qCAST_dir = "C:\\Users\\jnunezr\\Desktop\\qCAST"
	make_folder(C_qCAST_dir)

	print("synching windows files...")
	for parent, folders, files in os.walk(qCAST_dir):

		# skip the other outdirs
		if "outdir_mac" in parent or "outdir_linux" in parent: continue

		# define the C_parent
		C_parent = parent.replace(qCAST_dir, C_qCAST_dir)

		# skip some files
		if any([x.startswith(".") or x.startswith("__") for x in parent.split("\\")]): continue

		# make folders
		for f in folders: 
			if f.startswith(".") or f.startswith("__") or "outdir_mac" in f or "outdir_linux" in f: continue
			make_folder("%s\\%s"%(C_parent, f))

		# make files
		for f in files:
			if f.startswith("."): continue
			if not os.path.isfile("%s\\%s"%(C_parent, f)) or not ".tif" in f:
				shutil.copy("%s\\%s"%(parent, f), "%s\\%s"%(C_parent, f))

	# define the CurDir where to run
	CurDir = "%s%stesting%stesting_subset"%(C_qCAST_dir, sep, sep)

else: CurDir = "%s%stesting%stesting_subset"%(qCAST_dir, sep, sep)

# define dirs
main_py = "%s%s..%s..%smain.py"%(CurDir, sep, sep, sep)
outdir = "%s%soutdir_%s"%(CurDir, sep, operating_system)
strains = "%s%sstrains.xlsx"%(CurDir, sep)
drugs = "%s%sdrugs.xlsx"%(CurDir, sep)

make_folder(outdir)

# run the modules
print("running main.py")

# get plate layout
plate_layout = "%s%sget_plate_layout%splate_layout_long.xlsx"%(outdir, sep, sep)
if file_is_empty(plate_layout): 

	run_cmd("%s %s --os %s --module get_plate_layout --output %s%sget_plate_layout --docker_image mikischikora/qcast:v0.1 --strains %s --drugs %s"%(python_exec, main_py, operating_system, outdir, sep, strains, drugs))

# run images
run_cmd("%s %s --os %s --module analyze_images --output %s%simage_analysis --docker_image mikischikora/qcast:v0.1 --plate_layout %s --images %s%ssubset_raw_images --keep_tmp_files"%(python_exec, main_py, operating_system, outdir, sep, plate_layout, CurDir, sep))






