# Timekeeper, keeps track of time

import datetime
import pathlib

from typing import Optional


class Day(object):
    """
    Class containing objects and logic for handling a day of timekeeping
    """

    def __init__(self, date: Optional[datetime.date] = None):
        if date is None:
            date = datetime.date.today()
        self.date = date
        self.file = self._get_file()
        self.transitions = self._load()

    def _get_file(self):
        home = pathlib.Path.home()
        the_dir = home / ".timekeeper" / \
            str(self.date.year) / str(self.date.month)
        if not the_dir.exists():
            the_dir.mkdir(parents=True)
        the_file = the_dir / str(self.date.day)
        return the_file

    def _load(self):
        vals = []
        if self.file.exists():
            with open(self.file, "r", encoding="UTF-8") as inf:
                for line in inf.readlines():
                    if len(line) != 0:
                        try:
                            timestr, task, state = line.split(",")
                            the_time = datetime.datetime.strptime(
                                timestr, "%H:%M")
                            # Get to the date
                            the_time = the_time.replace(
                                year=self.date.year, month=self.date.month, day=self.date.day)
                            vals.append((the_time, task, state.strip()))
                        except Exception as exp:
                            print("Error reading line!" + line, exp)

        return vals

    def inout(self, inout: str, task: str = "work", the_time: Optional[datetime.datetime] = None):
        """
        Clock in or out
        """
        the_time = fix_time(the_time)
        if task is None:
            task = 'work'
        inout = inout.upper()
        if inout == "OUT":
            self.transitions.append((the_time, task, "IN"))
        elif inout == "IN":
            self.transitions.append((the_time, task, "OUT"))
        else:
            raise Exception("Must either clock in or out!")
        self.save()

    def get_state(self):
        """
        Get the current state of the days time
        """
        if len(self.transitions) == 0:
            return "OUT"
        else:
            return self.transitions[-1][2]

    def stat(self):
        for i in self.transitions:
            print(i)

    def save(self):
        """
        Write out the information to the file
        """
        the_file = self._get_file()
        with open(the_file, 'w', encoding="UTF-8") as outf:
            for atime, task, action in self.transitions:
                outf.write(atime.strftime("%H:%M"))
                outf.write(",")
                outf.write(task)
                outf.write(",")
                outf.write(action)
                outf.write("\n")


def fix_time(the_time: Optional[datetime.datetime] = None):
    """
    Make sure the time is okay
    """
    if the_time is None:
        the_time = datetime.datetime.now()
    the_time.replace(second=0)
    return the_time
