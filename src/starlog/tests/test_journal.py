import ipywidgets

from starlog import journal

from hamcrest import assert_that, equal_to, contains_exactly, anything, has_item
import unittest
from unittest import mock
from twisted.internet import task
import tempfile
import shutil
import os


class TestJournalTo(unittest.TestCase):

    def setUp(self):
        self.reactor = task.Clock()
        self.runner = mock.MagicMock()
        self.title = "Title"
        dirname = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, dirname)
        self.fname = os.path.join(dirname, "dummy-journal.txt")

    def test_basic_journaling(self):
        box = journal.journal_to(
            aspects=dict(default="Default"),
            title=self.title,
            fname=self.fname,
            reactor=self.reactor,
            runner=self.runner,
        )
        title, *things, output = box.children
        section_title, section_text, section_clock = things
        section_text.set_trait("value", "some tex")
        self.reactor.advance(11)
        section_text.set_trait("value", "some text\n")
        results = "".join(
            x["text"] for x in output.outputs if x["name"] == "stdout"
        )
        with open(self.fname) as fpin:
            journaled_data = fpin.read()
        commands = [x[0][0] for x in self.runner.call_args_list]
        assert_that(results, equal_to("Saving...Done\n"))
        assert_that(journaled_data.splitlines(), has_item("some text"))
        assert_that(
            commands,
            contains_exactly(
		contains_exactly("git", "add", self.fname),
                contains_exactly("git", "commit", "-m", anything()),
                contains_exactly("git", "push"),
            )
        )

    def test_running_clock(self):
        box = journal.journal_to(
            aspects=dict(default="Default"),
            title=self.title,
            fname=self.fname,
            reactor=self.reactor,
            runner=self.runner,
        )
        title, *things, output = box.children
        section_title, section_text, section_clock = things
        for i in range(10):
            print("about to advance")
            section_text.set_trait("value", "lalala "+ str(i))
            self.reactor.advance(60)
        with open(self.fname) as fpin:
            journaled_data = fpin.read()
        raise ValueError(journaled_data, section_clock.value)
