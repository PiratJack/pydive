"""Interface to get information about stored dives (from a divelog)

Classes
----------
DiveLog
    Represents a divelog file & its dives
DiveTrip
    Represents a trip containing multiple dives
Dive
    Represents a single dive from the divelog
"""
import os
import gettext
import logging
import xml.etree.ElementTree
import datetime

_ = gettext.gettext
logger = logging.getLogger(__name__)


class DiveLog:
    """Interface to get information about stored dives (from a divelog)

    Attributes
    ----------
    file_path : str
        Path to the dive log file
    dives : list of Dive and Trip
        All dives & trips of this divelog

    Methods
    -------
    __init__
        Defines default attributes
    load_dives
        Loads all dives from the divelog file
    """

    def __init__(self, divelog_file=None):
        """Defines default attributes"""
        logger.debug("DiveLog.init")
        self.file_path = divelog_file
        self.dives = []
        if self.file_path:
            self.load_dives()

    def load_dives(self, path=None):
        """Loads all dives from the stored divelog file"""
        # Find all pictures
        logger.info(f"DiveLog.load_dives {path}")
        self.dives = []
        if path:
            self.file_path = path
        if not self.file_path:
            raise ValueError(_("Please select a divelog file in the settings screen"))
        if not os.path.isfile(self.file_path):
            raise IOError(_("The divelog is not a file"))
        try:
            xml_tree = xml.etree.ElementTree.parse(self.file_path)
            xml_root = xml_tree.getroot()
            xml_dives = xml_root.find("dives")

            for child in xml_dives:
                if child.tag == "dive":
                    self.dives.append(Dive(child))
                elif child.tag == "trip":
                    self.dives.append(DiveTrip(child))
        except:
            raise ValueError(_("The divelog file could not be read"))


class DiveTrip:
    """Represents a trip containing multiple dives

    Attributes
    ----------
    type : str
        This object's type, used to distinguish from Dive (always "trip")
    name : str
        The name (location) of this trip
    dives : list of Dive
        The dives made during that trip
    start_time : datetime.time
        When the dive started

    Methods
    -------
    __init__ (xml_data)
        Parses the information of the dive from XML data
    """

    type = "trip"

    def __init__(self, xml_data):
        """Parses the information of the dive from XML data

        Parameters
        -------
        xml_data : xml.etree.Element
            The XML data for this dive
        """
        logger.debug("DiveTrip.init")
        self.dives = []
        self.start_date = None

        # Get name
        self.name = xml_data.attrib.get("location", "")

        # Parse date/time
        self.start_date = None
        time_iso = ""
        # Both attributes are mandatory, so no need to handle other cases
        if "date" in xml_data.attrib and "time" in xml_data.attrib:
            time_iso = xml_data.attrib["date"] + "T" + xml_data.attrib["time"]
        if time_iso:
            self.start_date = datetime.datetime.fromisoformat(time_iso)

        # Parse dives
        for child in xml_data:
            if child.tag == "dive":
                self.dives.append(Dive(child))


class Dive:
    """Represents a single dive from the divelog

    Attributes
    ----------
    type : str
        This object's type, used to distinguish from Dive (always "trip")
    max_depth : float
        The maximum depth reached
    duration : datetime.time
        The duration of the whole dive
    start_date : datetime.time
        When the dive started
    number : int
        The dive number

    Methods
    -------
    __init__ (xml_data, trip=None)
        Parses the information of the dive from XML data
    """

    type = "dive"

    def __init__(self, xml_data):
        """Parses the information of the dive from XML data

        Parameters
        -------
        xml_data : xml.etree.Element
            The XML data for this dive
        """
        logger.debug("Dive.init")

        # Parse max depth
        self.max_depth = 0
        depth = xml_data.find("divecomputer/depth")
        if depth is not None:
            self.max_depth = float(depth.attrib.get("max", 0).replace(" m", ""))

        # Parse duration
        self.duration = datetime.timedelta()
        duration = xml_data.attrib.get("duration", 0)
        if duration:
            duration = duration.replace(" min", "")
            minutes, seconds = map(int, duration.split(":"))
            hours = minutes // 60
            minutes %= 60
            self.duration = datetime.timedelta(
                hours=hours, minutes=minutes, seconds=seconds
            )

        # Parse depth/time
        self.depths = {}
        samples = xml_data.findall("divecomputer/sample")
        if samples:
            for sample in samples:
                sample_time = sample.attrib.get("time", 0).replace(" min", "")
                minutes, seconds = map(int, sample_time.split(":"))
                sample_time = minutes * 60 + seconds
                sample_depth = float(sample.attrib.get("depth", 0).replace(" m", ""))
                self.depths[sample_time] = sample_depth

        # Parse date/time
        self.start_date = None
        time_iso = ""
        # Both attributes are mandatory, so no need to handle other cases
        if "date" in xml_data.attrib and "time" in xml_data.attrib:
            time_iso = xml_data.attrib["date"] + "T" + xml_data.attrib["time"]
        if time_iso:
            self.start_date = datetime.datetime.fromisoformat(time_iso)

        # Parse number
        self.number = int(xml_data.attrib.get("number", 0))

        # Is there a picture linked to it?
        self.has_picture = xml_data.find("picture") is not None
