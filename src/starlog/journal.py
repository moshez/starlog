import functools
import subprocess
import datetime
import ipywidgets

from twisted.internet import task, reactor

runner = functools.partial(
    subprocess.run,
    capture_output=True,
    text=True,
    check=True
)

class DoneError(Exception):
    pass

def decrement_count(initial_value, label):
    current_value = initial_value
    minute = datetime.timedelta(minutes=1)
    def decrement(count):
        nonlocal current_value
        current_value -= count
        time_left = datetime.timedelta(seconds=max(current_value, 0))
        minutes, left = divmod(time_left, minute)
        seconds = int(left.total_seconds())
        label.value = f" Time left: {minutes}:{seconds:02}"
        if current_value < 0:
            raise DoneError("finished")
    return decrement

def journal_to(title, fname, reactor, runner):
    textarea = ipywidgets.Textarea(continuous_update=False)
    textarea.rows = 20
    clock = ipywidgets.Label("Time left:")
    output = ipywidgets.Output()
    box = ipywidgets.VBox([
        ipywidgets.Label(title),
        textarea,
        clock,
        output
    ])
    total_seconds = datetime.timedelta(minutes=5).total_seconds()
    call = task.LoopingCall.withCount(
        decrement_count(total_seconds,
        clock
    ))
    call.reactor = reactor
    done = call.start(1)
    done.addErrback(lambda x: x.trap(DoneError))
    def run(*args):
        runner(list(args))
    def saver(_ignored):
        with open(fname, "w") as fpout:
            fpout.write(textarea.value)
        output.append_stdout("Saving...")
        try:
            run("git", "add", fname)
            run("git", "commit", "-m", f"updated {fname}")
            run("git", "push")
        except subprocess.CalledProcessError as exc:
            output.append_stdout("\nCould not save:\n")
            output.append_stdout(exc.stdout)
            output.append_stdout(exc.stderr)
        else:
            output.append_stdout("Done\n")
    textarea.observe(saver, names="value")
    done.addCallback(saver)
    return box

def journal_date(today, runner, reactor):
    date = str(today())
    title = f"Starlog {date}"
    filename = f"{date}.txt"
    return journal_to(title, filename, reactor, runner)

journal = functools.partial(journal_date, datetime.date.today, runner, reactor)
