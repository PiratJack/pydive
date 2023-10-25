import os
import sys
import datetime
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "pydive"))


class TestDiveLog:
    def test_gets(self, pydive_divelog):
        # Check all elements
        assert len(pydive_divelog.dives) == 8, "Correct number of elements loaded"

        # Check a given dive
        dive = pydive_divelog.dives[0]
        assert dive.type == "dive", "Element identified as dive correctly"
        assert dive.max_depth == 6, "Dive max depth correct"
        assert dive.duration == datetime.timedelta(minutes=15), "Dive duration correct"
        start_date = datetime.datetime.fromisoformat("2002-07-24T14:00:06")
        assert dive.start_date == start_date, "Dive start time correct"
        assert dive.number == 0, "Dive number correct"

        # Check a given trip
        trip = pydive_divelog.dives[2]
        assert trip.type == "trip", "Element identified as trip correctly"
        assert trip.name == "Cavalaire", "Trip name correct"
        assert len(trip.dives) == 6, "Trip count of dives correct"
        start_date = datetime.datetime.fromisoformat("2019-10-04T10:49:05")
        assert trip.start_date == start_date, "Dive start time correct"


if __name__ == "__main__":
    pytest.main(["-s", __file__])
