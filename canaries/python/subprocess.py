import subprocess
import sys

subprocess.call("grep -R {} .".format(sys.argv[1]), shell=True)

github_token = "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"
