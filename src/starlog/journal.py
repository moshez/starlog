import functools
import subprocess
import datetime
import io
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

def decrement_count(initial_value, label, get_text):
    current_value = initial_value
    minute = datetime.timedelta(minutes=1)
    last_text = get_text()
    def decrement(count):
        nonlocal current_value
        nonlocal last_text
        new_text = get_text()
        if new_text == last_text:
            return
        last_text = new_text
        current_value -= count
        time_left = datetime.timedelta(seconds=max(current_value, 0))
        minutes, left = divmod(time_left, minute)
        seconds = int(left.total_seconds())
        label.value = f" Time left: {minutes}:{seconds:02}"
        if current_value < 0:
            raise DoneError("finished")
    return decrement

def run_timer(total_seconds, get_text, reactor):
    clock = ipywidgets.Label("Time left:")
    call = task.LoopingCall.withCount(
        decrement_count(
            total_seconds,
            clock,
            get_text
    ))
    call.reactor = reactor
    done = call.start(1)
    done.addErrback(lambda x: x.trap(DoneError))
    return done, clock

def make_text_areas(aspects):
    def get_text():
        res = io.StringIO()
        for key, (desc, area) in areas.items():
            print(desc, file=res)
            print("="*len(desc), file=res)
            print("", file=res)
            print(area.value, file=res)
        return res.getvalue()
    areas = dict()
    widgets = []
    for name, desc in aspects.items():
        textarea = ipywidgets.Textarea()
        textarea.rows = 15
        areas[name] = desc, textarea
        widgets.append(textarea)
    return widgets, get_text

def debouncer(reactor, func, interval):
    last_called = reactor.seconds()
    def maybe_call(*args, **kwargs):
        nonlocal last_called
        now = reactor.seconds()
        try:
            if now - last_called < interval:
                return
            func()
        finally:
            last_called = now
    return maybe_call

def saver(fname, get_text, output, runner):
    def run(*args):
        runner(list(args))
    with open(fname, "w") as fpout:
        fpout.write(get_text())    
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

def journal_to(aspects, title, fname, reactor, runner):
    widgets, get_text = make_text_areas(aspects)
    output = ipywidgets.Output()
    save_file = functools.partial(saver, fname, get_text, output, runner)
    maybe_save = debouncer(reactor, save_file, 10)
    quickly_save = debouncer(reactor, save_file, 0)
    total_seconds = datetime.timedelta(minutes=5).total_seconds()
    done, clock = run_timer(total_seconds, get_text, reactor)
    elements = [ipywidgets.Label(title)]
    for desc, widget in zip(aspects.values(), widgets):
        elements.append(ipywidgets.Label(desc))
        elements.append(widget)
        elements.append(clock)
        widget.observe(maybe_save, names="value")
    elements.append(output)
    done.addCallback(quickly_save)
    return ipywidgets.VBox(elements)


def journal_date(aspects, today, runner, reactor):
    date = str(today())
    title = f"Starlog changed {date}"
    filename = f"{date}.txt"
    return journal_to(aspects, title, fname=filename, reactor=reactor, runner=runner)

journal = functools.partial(journal_date, today=datetime.date.today, runner=runner, reactor=reactor)
