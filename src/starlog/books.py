from __future__ import annotations

import ipywidgets
import attr
import re
import functools
import httpx
import uuid
import traitlets
import pathlib

@attr.s(auto_attribs=True)
class UIBuilder:
    _widgets : Dict[str, Any] = attr.ib(init=False, factory=dict)
        
    def add_widgets(self, **kwargs):
        for name, widget in kwargs.items():
            self._widgets[name] = widget
        
    def __getattr__(self, name):
        if name.startswith("ui_"):
            return self._widgets[name[3:]]
        raise AttributeError(name)

DIGITS = re.compile("\d+")

def check_valid(client, isbn, valid, title, _ignored):
    entry = isbn.value
    all_digits = "".join(x.group() for x in DIGITS.finditer(entry))
    if len(all_digits) != 13:
        valid.value = False
        return
    valid.value = True
    parsed_isbn = isbn.traits()["parsed_isbn"]
    parsed_isbn.set(isbn, all_digits)
    book = client.get(f"https://openlibrary.org/isbn/{all_digits}.json").json()
    title.value = book["title"]

def header(builder):
    client = httpx.Client()
    builder.add_widgets(
        isbn=ipywidgets.Combobox(
            placeholder='',
            options=[''],
            description='ISBN:',
            ensure_option=False,
            disabled=False
        ),
        valid_isbn=ipywidgets.Valid(
            value=False,
            description="",
        ),
        title=ipywidgets.Label(
        )
    )
    builder.ui_isbn.add_traits(parsed_isbn=traitlets.Unicode())
    builder.ui_isbn.observe(
        functools.partial(check_valid, client, builder.ui_isbn, builder.ui_valid_isbn, builder.ui_title)
    )
    builder.add_widgets(
        header=ipywidgets.HBox([
         builder.ui_isbn,
         builder.ui_valid_isbn,
         builder.ui_title,
        ])
    )

def editor(builder):
    builder.add_widgets(
        main=ipywidgets.Textarea(rows=20, continuous_update=False),
        output=ipywidgets.Output(),
    )
    builder.ui_main.add_traits(filename=traitlets.Unicode(str(uuid.uuid4())))

def new_text(_ignored, path, main, isbn, valid_isbn, output):
    with output:
        filebase = main.trait_values()["filename"]
        if not valid_isbn.value:
            print("not saving, no isbn")
            return
        parsed_isbn = isbn.trait_values()["parsed_isbn"]
        filepath = path / f"{parsed_isbn}-{filebase}.txt"
        with open(filepath, "w") as fpout:
            fpout.write(main.value)
        print("Saved", filepath)

def get_existing_isbns(path):
    for child in path.glob("*.txt"):
        yield child.name.split("-")[0]

def combine(path, builder):
    header(builder)
    editor(builder)
    builder.ui_main.observe(
        functools.partial(new_text,
            path=path,
            main=builder.ui_main,
            isbn=builder.ui_isbn,
            valid_isbn=builder.ui_valid_isbn,
            output=builder.ui_output,
        ),
        names=["value"],
    )
    options = builder.ui_isbn.traits()["options"]
    existing = tuple(get_existing_isbns(pathlib.Path(".")))
    options.set(builder.ui_isbn, existing)
    builder.add_widgets(
        journal=ipywidgets.VBox([
           builder.ui_header,
           builder.ui_main,
           builder.ui_output,
        ])
    )

def book():
    builder = UIBuilder()
    combine(pathlib.Path.cwd(), builder)
    return builder.ui_journal

