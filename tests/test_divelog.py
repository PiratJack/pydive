import os
import sys
import pytest
import logging
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "pydive"))

from models.divelog import DiveLog

logging.basicConfig(level=logging.WARNING)

DATABASE_FILE = "test.sqlite"
DIVELOG_FILE = os.path.join(BASE_DIR, "..", "Carnet", "test_divelog.xml")


try:
    os.remove(DATABASE_FILE)
except OSError:
    pass


class TestDiveLog:
    def test_gets(self):
        # Load everything
        divelog = DiveLog(DIVELOG_FILE)

        # Check all elements
        assert len(divelog.dives) == 8, "Correct number of elements loaded"

        # Check a given dive
        dive = divelog.dives[0]
        assert dive.type == "dive", "Element identified as dive correctly"
        assert dive.max_depth == 6, "Dive max depth correct"
        assert dive.duration == datetime.timedelta(minutes=15), "Dive duration correct"
        start_time = datetime.datetime.fromisoformat("2002-07-24T14:00:06")
        assert dive.start_time == start_time, "Dive start time correct"
        assert dive.number == 0, "Dive number correct"

        # Check a given trip
        trip = divelog.dives[2]
        assert trip.type == "trip", "Element identified as trip correctly"
        assert trip.name == "Cavalaire", "Trip name correct"
        assert len(trip.dives) == 6, "Trip count of dives correct"
        start_time = datetime.datetime.fromisoformat("2019-10-04T10:49:05")
        assert trip.start_time == start_time, "Dive start time correct"

    def test_error_no_file(self):
        # Load everything
        divelog = DiveLog()


if __name__ == "__main__":
    pytest.main(["-s", __file__])
