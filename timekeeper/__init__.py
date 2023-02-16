"""Timekeeper, keeps track of time"""

import datetime
import pathlib

from collections import namedtuple
from typing import Optional, Tuple

Action = namedtuple("Action", ["time", "task", "inout"])


class TimeKeeperException(Exception):
    """
    Capture exceptions
    """

    def __init__(self, message="An error occured"):
        self.message = message
        super().__init__(self.message)


class Day:
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

    def _load(self) -> list[Action]:
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
                            vals.append(Action(the_time, task, state.strip()))
                        except Exception as exp:
                            raise TimeKeeperException(
                                "Error reading line: " + line) from exp
        return vals

    def inout(self, inout: str, task: str = "work", the_time: Optional[datetime.datetime] = None):
        """
        Clock in or out
        """
        the_time = fix_time(self.date, the_time)
        if task is None:
            task = 'work'
        inout = inout.upper()
        if inout == "OUT":
            # Ensure we are clocked in
            if len(self.transitions) < 1:
                raise TimeKeeperException(
                    "Cannot clock out, when not clocked in!")

            stat = self.transitions[-1].inout
            old_task = self.transitions[-1].task
            if stat != "IN":
                raise TimeKeeperException(
                    "Cannot log out, when logged not logged in")
            self.transitions.append(Action(the_time, old_task, "OUT"))
        elif inout == "IN":
            # Log out of old task if we need to first
            if len(self.transitions) > 0:
                if self.transitions[-1].inout == "IN":
                    self.transitions.append(
                        Action(the_time, self.transitions[-1].task, "OUT"))

            self.transitions.append(Action(the_time, task, "IN"))
        else:
            raise TimeKeeperException("Must either clock in or out!")
        self.validate()
        self.save()

    def validate(self):
        """
        Validate that we are in a good state
        """
        if len(self.transitions) > 0:
            current = self.transitions[0]
            # Check that the first action of the day is in
            if current.inout != "IN":
                raise TimeKeeperException("First action of day must be in!")
            for i in self.transitions[1:]:
                # Check backwards time
                if i.time < current.time:
                    raise TimeKeeperException(
                        "Time went backward, that's not good")
                if current.inout == 'IN':
                    # Check that we are clocking of the current
                    # job before clocking into the next one
                    if i.inout != "OUT":
                        raise TimeKeeperException(
                            "Must clock out before you can clock into next job")
                    # Check that we aren't clocking out of a different job
                    if i.task != current.task:
                        raise TimeKeeperException(
                            "Cannot clock out of job you are not working")
                if current.inout == 'OUT' and i.inout == 'OUT':
                    raise TimeKeeperException(
                        "Must clock in before you can clock out")
                current = i

    def collect_times(self) -> Tuple[datetime.timedelta, dict]:
        """
        Return the total time tracked, and a dictonary of times by task
        """
        self.validate()
        by_task = {}
        total_time = datetime.timedelta(hours=0)
        trans = self.transitions[:]
        if len(trans) > 0:
            if trans[-1].inout == 'IN':
                trans.append(
                    Action(datetime.datetime.now().replace(second=0, microsecond=0),
                           self.transitions[-1].task, "OUT"))
        for idx in range(0, len(trans), 2):
            start = trans[idx]
            stop = trans[idx+1]
            delta = stop.time - start.time
            total_time += delta
            if start.task in by_task:
                # Store task time and time in/out pairs there
                task_time, pairs = by_task[start.task]
                task_time += delta
                pairs.append((start.time, stop.time))
                by_task[start.task] = (task_time, pairs)
            else:
                by_task[start.task] = (delta, [(start.time, stop.time)])
        return total_time, by_task

    def stat(self):
        """
        Don't save after calling this function, it adds a transition to the last time
        Assumes that validation has already happened, so we can have happy little in/out pairs
        """
        total_time, by_task = self.collect_times()
        print("----------------------")
        print(f"Time for: {self.date:%Y-%m-%d}")
        print(f"Total: {delta_to_hour_min(total_time)}")
        print("----------------------")
        for task, value in by_task.items():
            total = delta_to_hour_min(value[0])
            info = ", ".join([(st.strftime("%H:%M") + '->' + et.strftime("%H:%M"))
                              for st, et in value[1]])
            print(f"{task} ==> {total}\n\tTimes: {info}")

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


def fix_time(date: datetime.date, the_time: Optional[datetime.datetime] = None):
    """
    Make sure the time is okay
    """
    if the_time is None:
        the_time = datetime.datetime.now()
    # Zero out seconds, put into the right day
    return the_time.replace(second=0, year=date.year, month=date.month, day=date.day)


def delta_to_hour_min(delta: datetime.timedelta) -> str:
    """
    Convert timedelta to hour:minute string
    """
    hours = delta.days * 24
    hours += delta.seconds // 60 // 60
    minutes = (delta.seconds // 60) % 60
    return f"{hours}:{minutes:02}"
