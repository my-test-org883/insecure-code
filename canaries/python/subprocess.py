import subprocess
import sys

subprocess.call("grep -R {} .".format(sys.argv[1]), shell=True)

my-github-token = "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"
