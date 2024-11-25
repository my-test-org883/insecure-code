import subprocess
import sys

subprocess.call("grep -R {} .".format(sys.argv[1]), shell=True)

my_gitlab_token = "glpat-6_sGncEHLPY1Ujn8rZYi"
