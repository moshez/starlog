import datetime
import pathlib
import textwrap
import sys

def ctime(log):
    return datetime.datetime.fromisoformat(log.stem)

def print_logs(path, current, outfile):
    cutoff =  current - datetime.timedelta(days=7)
    recent_files = [
        log
        for log in path.glob("*.txt")
        if ctime(log) > cutoff
    ]
    recent_files.sort()
    for log in recent_files:
        text = log.read_text()
        text = textwrap.fill(text)
        print(log.name, "\n\n", text, "\n", file=outfile)
