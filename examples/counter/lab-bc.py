import atexit
import getopt
import os
import subprocess
import signal
import sys
import time
import pathlib
import platform

progname = sys.argv[0]

diagnostics = False
quiet = False
verbose = False

port = 80
machine = "eecs-digital-56.mit.edu"
projectdir = "."
of = "obj"

p = False

user = "builder"
outfile = f"{of}/out.bit"
logfile = f"{of}/build.log"

synthrpt = [
		"report_timing",
		"report_timing_summary",
		"report_utilization",
	   ]

placerpt = synthrpt.copy()
placerpt.extend(['report_clock_utilization'])

routerpt = [
		'report_drc',
		'report_power',
		'report_route_status',
		'report_timing',
		'report_timing_summary',
	   ]

usagestr = f"""
{progname}: build SystemVerilog code remotely for 2022 6.205 labs
usage: {progname} [-dqv] [-m machine] [-p projectdir] [-o dir]
options:
	-d: emit additional diagnostics during synthesis/implementation
	-q: quiet: do not generate any vivado logs except for errors.
	-v: be verbose (for debugging stuffs / if you see a bug)
	-m: override the DNS name queried to perform the build. use with care.
	-p: build the project located in projectdir (default is '.')
	-o: set the output products directory (default is {of})
"""

def debuglog(s):
	if verbose: print(s)

def usage():
	print(usagestr)
	sys.exit(1)

def getargs():
	global diagnostics
	global quiet
	global machine
	global logfile
	global outfile
	global projectdir
	global of
	global verbose

	try:
		opts, args = getopt.getopt(sys.argv[1:], "dm:o:p:qv")
	except getopt.GetoptError as err:
		print(err)
		usage()

	if args: usage()
	for o, v in opts:
		if o == '-d': diagnostics = True
		elif o == '-q': quiet = True
		elif o == '-m': machine = v
		elif o == '-p': projectdir = v
		elif o == '-o': of = v
		elif o == '-v': verbose = True
		else:
			print(f"unrecognized option {o}")
			usage()

	outfile = f"{of}/out.bit"
	logfile = f"{of}/build.log"

def make_posix(path):
	return str(pathlib.Path(path).as_posix())

def regfiles():
	ftt = {}
	debuglog(f"projectdir is {projectdir}")
	for dirpath, subdirs, files in os.walk(projectdir):
		if 'src' not in dirpath and 'xdc' not in dirpath and 'data' not in dirpath and 'ip' not in dirpath:
			continue 
		if dirpath.startswith("./"): dirpath = dirpath[2:]
		for file in files:
			fpath = os.path.join(dirpath, file)
			debuglog(f"considering {fpath}")
			fpath = make_posix(fpath)

			if file.lower().endswith('.v'): ftt[fpath] = 'source'
			elif file.lower().endswith('.sv'): ftt[fpath] = 'source'
			elif file.lower().endswith('.vh'): ftt[fpath] = 'source'
			elif file.lower().endswith('.svh'): ftt[fpath] = 'source'
			elif file.lower().endswith('.xdc'): ftt[fpath] = 'xdc'
			elif file.lower().endswith('.mem'): ftt[fpath] = 'mem'
			elif file.lower().endswith('.xci'): ftt[fpath] = 'ip'
			elif file.lower().endswith('.prj'): ftt[fpath] = 'mig'

	debuglog(f"elaborated file list {ftt}")
	return ftt

# messages are newline delineated per lab-bs.1
# utilize this to cheat a little bit
def spqsend(p, msg):
	debuglog(f"writing {len(msg)} bytes over the wire")
	debuglog(f"full message: {msg}")
	p.stdin.write(msg + b'\n')
	p.stdin.flush()

def spsend(p, msg):
	debuglog(f"running {msg}")
	p.stdin.write((msg + '\n').encode())
	p.stdin.flush()

def sprecv(p):
	l = p.stdout.readline().decode()
	debuglog(f"got {l}")
	return l

def xsprecv(p):
	l = sprecv(p)
	if (l.startswith("ERR")):
		print("received unexpected server error!")
		print(l)
		sys.exit(1)
	return l

def spstart(xargv):
	debuglog(f"spawning {xargv}")
	p = subprocess.PIPE
	return subprocess.Popen(xargv, stdin=p, stdout=p, stderr=p)

def copyfiles(p, ftt):
	for f, t in ftt.items():
		fsize = os.path.getsize(f)
		with open(f, 'rb') as fd:
			spsend(p, f"write {f} {fsize}")
			time.sleep(0.1) #?
			spqsend(p, fd.read())
			xsprecv(p)

			spsend(p, f"type {f} {t}")
			xsprecv(p)

# size message returns ... %zu bytes
def readfile(p, file, targetfile):
	spsend(p, f"size {file}")
	size = int(xsprecv(p).split()[-2])
	spsend(p, f"read {file}")

	with open(targetfile, 'wb+') as fd:
		fd.write(p.stdout.read(size))
	
	xsprecv(p)

def build(p):
	cmd = "build"
	if diagnostics: cmd += " -d"
	if quiet: cmd += " -q"
	cmd += f" obj"

	print(f"Output target will be {outfile}")

	spsend(p, cmd)
	print("Building your code ... (this may take a while, be patient)")
	result = sprecv(p)

	if result.startswith("ERR"): print("Something went wrong!")
	else:
		readfile(p, "obj/out.bit", outfile)
		print(f"Build succeeded, output at {outfile}")
	
	readfile(p, "obj/build.log", logfile)
	print(f"Log file available at {logfile}")

	if (diagnostics):
		for rpt in synthrpt:
			readfile(p, f"obj/synthrpt_{rpt}.rpt", f"{of}/synthrpt_{rpt}.rpt")
		for rpt in placerpt:
			readfile(p, f"obj/placerpt_{rpt}.rpt", f"{of}/placerpt_{rpt}.rpt")
		for rpt in routerpt:
			readfile(p, f"obj/routerpt_{rpt}.rpt", f"{of}/routerpt_{rpt}.rpt")
		print(f"Diagnostics available in {of}")

def main():
	global p
	getargs()
	ftt = regfiles()

	if not os.path.isdir(of):
		print(f"output path {of} does not exist! create it or use -o?")
		usage()
	
	if platform.system() == 'Darwin' or platform.system() == 'Linux':
		xargv = ['ssh', '-p', f"{port}", '-o', "StrictHostKeyChecking=no", '-o', 'UserKnownHostsFile=/dev/null']

	elif platform.system() == 'Windows':
		xargv = ['ssh', '-p', f"{port}", '-o', "StrictHostKeyChecking=no", '-o', 'UserKnownHostsFile=nul']

	else:
		raise RuntimeError('Your OS is not recognized, unsure of how to format SSH command.')
	
		
	xargv.append(f"{user}@{machine}")
	p = spstart(xargv)

	spsend(p, "help")
	result = xsprecv(p)
	debuglog(result)

	copyfiles(p, ftt)
	build(p)
	spsend(p, "exit")
	p.wait()	
				
if __name__ == "__main__":
	try: main()
	except (Exception, KeyboardInterrupt) as e:
		if p:
			debuglog("killing ssh")
			os.kill(p.pid, signal.SIGINT)
			p.wait()
		raise e
