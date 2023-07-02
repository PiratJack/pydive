"""Allows to access database & file system through a generic interface

Classes
----------
Repository
    Allows to access database & file system through a generic interface

ProcessGroup
    A group of background running processes

CopyProcess
    A process to copy pictures from one location to another

GenerateProcess
    A process to generate pictures from raw pictures

RemoveProcess
    A process to delete pictures

ProcessSignals
    Defines signals when processes are completed or in error
"""
import os
import shutil
import gettext
import logging

from PyQt5 import QtCore
from .picture import Picture as PictureModel
from .picturegroup import PictureGroup
from .storagelocation import StorageLocation

_ = gettext.gettext
logger = logging.getLogger(__name__)


class Repository:
    """Allows to access database & file system through a generic interface

    Attributes
    ----------
    allowed_extensions : list of str
        List of picture extensions that can be displayed

    Methods
    -------
    __init__
        Defines default attributes
    load_pictures (folders)
        Loads all pictures from the provided storage locations (folders)
    read_folder (pictures, location_name, path)
        Reads a given folder recursively to find pictures
    add_picture (picture_group, location, path)
        Adds a single picture to a given picture_group
    remove_picture (picture_group, location, path)
        Removes a picture from memory (not hard drive)
    copy_pictures (label, target_location, source_location, trip, picture_group, conversion_method)
        Copies pictures between folders
    generate_pictures (label, target_location, conversion_methods, source_location, trip, picture_group)
        Generates pictures by converting between different formats
    change_trip_pictures (label, target_trip, source_trip, picture_group)
        Moves pictures between folders (trips)
    change_trip_pictures_finished (source_picture_group, picture, target_picture_group)
        Triggers memory updates after a picture has been moved
    """

    allowed_extensions = [".cr2", ".jpg", ".jpeg"]

    def __init__(self):
        """Defines default attributes"""
        logger.debug("Repository.init")
        self.storage_locations = []
        self.picture_groups = []
        self.process_groups = []
        # TODO: Darktherapee prevents multithreading, hence this (ugly) workaround
        QtCore.QThreadPool.globalInstance().setMaxThreadCount(1)

    def load_pictures(self, storage_locations):
        """Loads all pictures from the provided storage locations (folders)

        Pictures are added in the corresponding picture_group

        Parameters
        ----------
        storage_locations : list of StorageLocation
            The storage locations
        """
        # Find all pictures
        logger.info(f"Repository.load_pictures in {storage_locations}")
        self.storage_locations += storage_locations.copy()
        self.storage_locations = list(set(self.storage_locations))
        self.picture_groups = []
        for location in self.storage_locations:
            pictures = self.read_folder([], location.path)
            for picture in pictures:
                matching_groups = [
                    group
                    for group in self.picture_groups
                    if (
                        picture.name.startswith(group.name)
                        or group.name.startswith(picture.name)
                    )
                    and picture.trip == group.trip
                ]
                # Group doesn't exist yet
                if len(matching_groups) == 0:
                    group = PictureGroup(picture.name)
                    self.picture_groups.append(group)
                    group.pictureGroupDeleted.connect(
                        lambda _a, _b, g=group: self.picture_groups.remove(g)
                    )
                else:
                    # There should not be multiple matching groups
                    # This is because groups are created in alphabetical order
                    # Therefore groups with shorter names are processed first
                    group = matching_groups[0]
                group.add_picture(picture)
            logger.info(
                f"Repository.load_pictures: found {len(pictures)} images in {location.name}"
            )

    def read_folder(self, pictures, path):
        """Reads a given folder recursively to find pictures

        Parameters
        ----------
        pictures : list of Picture
            The list in which to add new pictures
        path : str
            The path to explore (will do nothing if it's not a folder)
        """
        logger.debug(f"Repository.read_folder init : {path}, {len(pictures)} pictures")
        if not os.path.isdir(path):
            return pictures
        for element in os.listdir(path):
            full_path = os.path.join(path, element)
            if os.path.isdir(full_path):
                self.read_folder(pictures, full_path)
            else:
                matching_extension = [
                    ext
                    for ext in self.allowed_extensions
                    if full_path.lower().endswith(ext)
                ]
                if matching_extension:
                    pictures.append(PictureModel(self.storage_locations, full_path))
        logger.debug(f"Repository.read_folder done : {path}, {len(pictures)} pictures")
        return pictures

    def add_picture(self, picture_group, location, path):
        """Adds a single picture to a given picture_group

        Note: this function does not create picture files

        Parameters
        ----------
        picture_group : PictureGroup
            The picture group in which to add the picture
        location : StorageLocation
            The storage location in which the picture is
        path : str
            The file path of the picture to add
        """
        logger.info(
            f"Repository.add_picture for {picture_group.trip}/{picture_group.name} in {location.name} - {path}"
        )
        picture = PictureModel([location], path)
        picture_group.add_picture(picture)

    def remove_picture(self, picture_group, location, path):
        """Removes a picture from memory (not hard drive)

        Parameters
        ----------
        picture_group : PictureGroup
            The picture group in which to add the picture
        location : StorageLocation
            Where the picture is stored
        path : str
            The file path on hard drive
        """
        logger.info(
            f"Repository.remove_picture from {picture_group.trip}/{picture_group.name} in {location.name} - {path}"
        )
        picture = [p for p in picture_group.locations[location.name] if p.path == path]
        if picture and len(picture) == 1:
            picture_group.remove_picture(picture[0])

    def copy_pictures(
        self,
        label,
        target_location,
        source_location=None,
        trip=None,
        picture_group=None,
        conversion_method=None,
    ):
        """Copies pictures between folders

        This function will create new picture files (by copying them)
        Triggers self.add_picture once the copy is complete

        Parameters
        ----------
        label : str
            The name of the process (used for display)
        target_location : StorageLocation
            The location in which pictures should be copied
        source_location : StorageLocation
            The source location in which pictures should be taken from
            Copies images from all locations if empty
        trip : str
            The trip to copy. Ignored if blank or if picture_group is provided.
            Either trip or picture_group must be provided
        picture_group : PictureGroup
            The picture group to copy. Ignored if blank.
            Either trip or picture_group must be provided
        conversion_method : str
            Copy only pictures with a specific conversion method. If blank, copies all pictures.

        Returns
        ----------
        process_group : ProcessGroup
            The group of background processes copying pictures
        """
        logger.info(f"Repository.copy_pictures {label}")
        logger.debug(
            f"#Args: {trip if trip is not None else '*'}/{picture_group.name if picture_group else '*'} from {source_location.name if source_location else '*'} to {target_location.name}{(' (only ' + conversion_method +')') if conversion_method else ''}"
        )
        # Determine all the picture groups to process
        picture_groups = None
        if picture_group:
            picture_groups = [picture_group]
            trip = picture_group.trip
        elif trip is not None:
            picture_groups = self.trips[trip].values()

        if not picture_groups:
            raise ValueError("trip or picture_group is required")

        # Determine the source: if same image exists, then it'll be a copy
        process_group = ProcessGroup(label)
        for picture_group in picture_groups:
            source_pictures = []
            if conversion_method:
                # If a conversion method is preferred: take the first available picture
                if conversion_method not in picture_group.pictures:
                    raise FileNotFoundError(_("No source image found"))

                source_pictures.append(picture_group.pictures[conversion_method][0])
            else:
                # Otherwise, just pick 1 picture for each available method
                for method in picture_group.pictures:
                    source_pictures.append(picture_group.pictures[method][0])

            # Generate tasks for each copy
            for source_picture in source_pictures:
                if (
                    source_location
                    and source_picture.location.name != source_location.name
                ):
                    continue
                process = CopyProcess(picture_group, source_picture, target_location)
                process.signals.taskFinished.connect(self.add_picture)
                process_group.add_task(process)
                QtCore.QThreadPool.globalInstance().start(process, 100)

        self.process_groups.append(process_group)
        return process_group

    def generate_pictures(
        self,
        label,
        target_location,
        conversion_methods,
        source_location=None,
        trip=None,
        picture_group=None,
    ):
        """Generates pictures by converting between different formats

        This function will create new picture files (by converting from RAW pictures)
        Triggers self.add_picture once the generation is complete

        Parameters
        ----------
        label : str
            The name of the process (used for display)
        target_location : StorageLocation
            The location in which pictures should be copied
        conversion_methods : list of ConversionMethod
            Uses those methods to convert
        source_location : StorageLocation
            The source location in which pictures should be taken from
            Copies images from all locations if empty
        trip : str
            The trip to copy. Ignored if blank or if picture_group is provided.
            Either trip or picture_group must be provided
        picture_group : PictureGroup
            The picture group to copy. Ignored if blank.
            Either trip or picture_group must be provided

        Returns
        ----------
        process_group : ProcessGroup
            The group of background processes generating pictures
        """
        # Determine all the picture groups to process
        logger.info(f"Repository.generate_pictures {label}")
        logger.debug(
            f"#Args: {trip if trip is not None else '*'}/{picture_group.name if picture_group else '*'} from {source_location.name if source_location else '*'} to {target_location.name} (only {conversion_methods})"
        )
        if picture_group:
            picture_groups = [picture_group]
            trip = picture_group.trip
        elif trip is not None:
            picture_groups = self.trips[trip].values()

        if not picture_groups:
            raise ValueError("trip or picture_group is required")

        # Determine the source: find the RAW image
        process_group = ProcessGroup(label)
        for picture_group in picture_groups:
            # Determine source (RAW) picture
            if "" not in picture_group.pictures:
                raise FileNotFoundError(_("No source image found"))
            if source_location:
                source_picture = [
                    p
                    for p in picture_group.pictures[""]
                    if p.location == source_location
                ]
                if not source_picture:
                    raise FileNotFoundError(
                        _("No source image found in specified location")
                    )
            else:
                source_picture = picture_group.pictures[""]
            source_picture = source_picture[0]

            # Generate tasks for each generation
            for conversion_method in conversion_methods:
                if (
                    source_location
                    and source_picture.location.name != source_location.name
                ):
                    continue

                process = GenerateProcess(
                    target_location, picture_group, source_picture, conversion_method
                )
                process.signals.taskFinished.connect(self.add_picture)
                process_group.add_task(process)
                QtCore.QThreadPool.globalInstance().start(process, 100)

        self.process_groups.append(process_group)
        return process_group

    def remove_pictures(
        self,
        label,
        trip=None,
        picture_group=None,
        picture=None,
    ):
        """Removes pictures from hard drive

        Triggers self.remove_picture once the process is complete

        Parameters
        ----------
        label : str
            The name of the process (used for display)
        trip : str
            The trip where the files are. Ignored if picture or picture_group is provided.
            Either trip, picture_group or picture must be provided
        picture_group : PictureGroup
            The picture group to copy. Required if picture is provided.
            Either trip, picture_group or picture must be provided
        picture : Picture
            The picture to copy.
            picture_group is required if picture is provided
            Either trip, picture_group or picture must be provided

        Returns
        ----------
        process_group : ProcessGroup
            The group of background processes deleting pictures
        """
        logger.info(f"Repository.remove_pictures {label}")
        logger.debug(
            f"#Args: {trip if trip is not None else '*'}/{picture_group.name if picture_group else '*'}/{picture.filename if picture else '*'}"
        )

        if not picture and not picture_group and trip is None:
            raise ValueError("Either trip, picture_group or picture must be provided")

        # Determine all the picture groups to process
        pictures = []
        picture_groups = []
        if picture:
            if not picture_group:
                raise ValueError("picture_group is required if picture is provided")
            pictures = [picture]
        if picture_group:
            picture_groups = [picture_group]
        elif trip is not None:
            picture_groups = self.trips[trip].values()

        # Determine the source: if same image exists, then it'll be a copy
        process_group = ProcessGroup(label)
        for picture_group in picture_groups:
            if picture:
                pictures = [picture]
            else:
                pictures = []
                for conversion_type in picture_group.pictures:
                    pictures += picture_group.pictures[conversion_type]
            for picture in pictures:
                # Generate tasks for each deletion
                process = RemoveProcess(picture_group, picture)
                process_group.add_task(process)
                process.signals.taskFinished.connect(self.remove_picture)
                QtCore.QThreadPool.globalInstance().start(process, 100)

        self.process_groups.append(process_group)
        return process_group

    def change_trip_pictures(
        self,
        label,
        target_trip,
        source_trip=None,
        picture_group=None,
    ):
        """Moves pictures between folders (trips)

        Triggers self.remove_picture and self.add_picture once the copy is complete

        Parameters
        ----------
        label : str
            The name of the process (used for display)
        target_trip : str
            The trip where the files should be transferred
        source_trip : str
            The trip where the files are. Ignored if blank or if picture_group is provided.
            Either source_trip or picture_group must be provided
        picture_group : PictureGroup
            The picture group to copy. Ignored if blank.
            Either source_trip or picture_group must be provided

        Returns
        ----------
        process_group : ProcessGroup
            The group of background processes copying pictures
        """
        logger.info(f"Repository.change_trip_pictures {label}")
        logger.debug(
            f"#Args: {picture_group.name if picture_group else '*'} from {source_trip if source_trip is not None else '*'} to {target_trip}"
        )
        # Determine all the picture groups to process
        picture_groups = None
        if picture_group:
            picture_groups = [picture_group]
            source_trip = picture_group.trip
        elif source_trip:
            picture_groups = self.trips[source_trip].values()

        if not picture_groups:
            raise ValueError("source_trip or picture_group is required")

        # Determine the source: if same image exists, then it'll be a copy
        process_group = ProcessGroup(label)
        for source_picture_group in picture_groups:
            # The target picture group may not be the source one
            # Or transfers may fail, thus we need to have both
            target_picture_group = [
                pg
                for pg in self.picture_groups
                if pg.trip == target_trip and pg.name == source_picture_group.name
            ]
            if target_picture_group:
                target_picture_group = target_picture_group[0]
            else:
                target_picture_group = PictureGroup(source_picture_group.name)
                target_picture_group.trip = target_trip
                self.picture_groups.append(target_picture_group)

            # Generate tasks for each move
            for conversion_type in source_picture_group.pictures:
                for source_picture in source_picture_group.pictures[conversion_type]:
                    process = ChangeTripProcess(
                        source_picture_group, source_picture, target_trip
                    )
                    process_group.add_task(process)

                    process.signals.taskFinished.connect(
                        lambda source_picture_group, _b, path, picture=source_picture, target_picture_group=target_picture_group: self.change_trip_pictures_finished(
                            source_picture_group, picture, path, target_picture_group
                        )
                    )
                    QtCore.QThreadPool.globalInstance().start(process, 100)

        self.process_groups.append(process_group)
        return process_group

    def change_trip_pictures_finished(
        self, source_picture_group, picture, path, target_picture_group
    ):
        """Triggers memory updates after a picture has been moved

        Triggers self.remove_picture and self.add_picture

        Parameters
        ----------
        source_picture_group : PictureGroup
            The source picture group of the image
        picture : Picture
            The modified picture
        path : str
            The new path of the picture
        target_picture_group : PictureGroup
            The target picture group of the image

        Returns
        ----------
        process_group : ProcessGroup
            The group of background processes copying pictures
        """
        logger.info("Repository.change_trip_pictures_finished")
        logger.debug(
            f"#Args: {source_picture_group}/{picture.filename} to {target_picture_group.name} - {path}"
        )
        self.remove_picture(source_picture_group, picture.location, picture.path)
        picture.trip = target_picture_group.trip
        picture.path = path
        self.add_picture(target_picture_group, picture.location, picture.path)

    def __getattr__(self, attr):
        """Calculates & returns missing attributes. Only works for trips attribute.

        Returns
        ----------
        trips : dict trip:picture_group.name:PictureGroup
            A dict representing all existing trips
        """
        if attr == "trips":
            trips = {}
            for picture_group in self.picture_groups:
                if picture_group.trip not in trips:
                    trips[picture_group.trip] = {}
                trips[picture_group.trip][picture_group.name] = picture_group
            return trips


class ProcessGroup(QtCore.QObject):
    """A group of process that share common attributes

    Methods
    -------
    __init__ (label)
        Stores basic information about the task group
    add_task (process)
        Adds a new task to the group
    task_done (task, path)
        Marks a single task as in done & stopped. Triggers self.update_progress
    task_error (task, error)
        Marks a single task as in error & stopped. Triggers self.update_progress
    update_progress
        Updates the progress. Emits finishes signal once complete.
    """

    finished = QtCore.pyqtSignal()

    def __init__(self, label):
        """Stores basic information about the task group

        Parameters
        ----------
        label : str
            The name of the task to display
        """
        logger.info(f"ProcessGroup.init {label}")
        super().__init__()
        self.progress = 0
        self.tasks = []
        self.label = label

    def add_task(self, process):
        """Adds a new task to the group

        Parameters
        ----------
        process : *Process
            The process to add
        """
        logger.debug("ProcessGroup.add_task")
        task = {"status": "Queued"}
        self.tasks.append(task)
        process.signals.taskFinished.connect(
            lambda _a, _b, path: self.task_done(task, path)
        )
        process.signals.taskError.connect(
            lambda _a, _b, error: self.task_error(task, error)
        )

    def task_done(self, task, path):
        """Marks a single task as in done & stopped. Triggers self.update_progress

        Parameters
        ----------
        task : *Process
            The task in error
        path : str
            The path of the newly created image
        """
        logger.debug("ProcessGroup.task_done")
        task["status"] = "Stopped"
        task["file_path"] = path
        self.update_progress()

    def task_error(self, task, error):
        """Marks a single task as in error & stopped. Triggers self.update_progress

        Parameters
        ----------
        task : *Process
            The task in error
        error : str
            The error message
        """
        logger.debug("ProcessGroup.task_error")
        task["status"] = "Stopped"
        task["error"] = error
        self.update_progress()

    def update_progress(self):
        """Updates the progress. Emits finished signal once complete."""
        done = len([t for t in self.tasks if t["status"] == "Stopped"])
        self.progress = done / len(self.tasks)
        if done == len(self.tasks):
            logger.info(f"ProcessGroup finished {self.label}")
            self.finished.emit()

    def __repr__(self):
        return (self.task_type, self.trip).__repr__()


class CopyProcess(QtCore.QRunnable):
    """A process to copy pictures between locations

    Methods
    -------
    __init__ (picture_group, source_picture, target_location)
        Stores the required parameters for the copy
    run
        Runs the copy, after making sure it won't create issues
    """

    def __init__(self, picture_group, source_picture, target_location):
        """Stores the required parameters for the copy

        Parameters
        ----------
        picture_group : PictureGroup
            The group of pictures to copy
        source_picture : Picture
            The source picture to copy
        target_location : StorageLocation
            The location where to copy the picture
        """
        logger.debug(
            f"CopyProcess.init {picture_group.trip}/{picture_group.name}/{source_picture.filename} to {target_location.name}"
        )
        super().__init__()
        self.signals = ProcessSignals()
        self.picture_group = picture_group
        self.target_location = target_location

        self.source_file = source_picture.path
        # Determine picture's target path
        self.target_file = os.path.join(
            target_location.path,
            source_picture.trip,
            source_picture.filename,
        )

    def __repr__(self):
        return "Copy task: " + self.source_file + " to " + self.target_file

    def run(self):
        """Runs the copy, after making sure it won't create issues

        Will emit error signal if target file already exists
        Will emit finished signal once copy is complete
        """
        # Check target doesn't exist already
        if os.path.exists(self.target_file):
            self.signals.taskError.emit(
                self.picture_group,
                self.target_location,
                _("Target file already exists"),
            )
            return

        # Run the actual processes
        os.makedirs(os.path.dirname(self.target_file), exist_ok=True)
        shutil.copy2(self.source_file, self.target_file)
        logger.info(
            f"CopyProcess finished {self.picture_group.trip}/{self.picture_group.name}/{os.path.basename(self.source_file)} to {self.target_location.name}"
        )
        self.signals.taskFinished.emit(
            self.picture_group,
            self.target_location,
            self.target_file,
        )


class GenerateProcess(QtCore.QRunnable):
    """A process to generate pictures from raw pictures

    Methods
    -------
    __init__ (location, picture_group, source_picture, method)
        Determines the actual system command to run
    run
        Runs the command, after making sure it won't create issues
    """

    def __init__(self, location, picture_group, source_picture, method):
        """Determines the actual system command to run

        Parameters
        ----------
        location : StorageLocation
            The location where the generation happens
        picture_group : PictureGroup
            The picture_group to update after the command runs
        source_picture : Picture
            The RAW picture to convert
        method : ConversionMethod
            The method to convert the image
        """
        logger.debug(
            f"GenerateProcess.init: {picture_group.trip}/{picture_group.name}/{source_picture.filename} to {location.name} using {method}"
        )
        super().__init__()
        self.signals = ProcessSignals()
        self.picture_group = picture_group
        self.location = location

        # Determine folder / file paths
        self.source_file = source_picture.path

        self.target_folder = os.path.join(location.path, picture_group.trip)
        target_file_name = source_picture.name + "_" + method.suffix + ".jpg"
        self.target_file = os.path.join(self.target_folder, target_file_name)

        # Let's mix all that together!
        command = method.command
        command = command.replace("%SOURCE_FILE%", self.source_file)
        command = command.replace("%TARGET_FILE%", self.target_file)
        command = command.replace("%TARGET_FOLDER%", self.target_folder)
        self.command = command

    def run(self):
        """Runs the command, after making sure it won't create issues

        Will emit error signal if target file already exists
        Will emit finished signal once process is complete
        """
        # Check target doesn't exist already
        if os.path.exists(self.target_file):
            self.signals.taskError.emit(
                self.picture_group,
                self.location,
                _("Target file already exists"),
            )
            return
        # Check target folder exists
        if not os.path.exists(self.target_folder):
            os.makedirs(self.target_folder, exist_ok=True)

        os.system(self.command)
        logger.info(
            f"GenerateProcess finished {self.picture_group.trip}/{self.picture_group.name}/{os.path.basename(self.source_file)} to {self.location.name}..{os.path.basename(self.target_file)}"
        )
        self.signals.taskFinished.emit(
            self.picture_group,
            self.location,
            self.target_file,
        )

    def __repr__(self):
        return "Generate task: " + self.command


class RemoveProcess(QtCore.QRunnable):
    """A process to delete pictures

    Methods
    -------
    __init__ (picture_group, picture)
        Determines the actual system command to run
    run
        Runs the command, after making sure it won't create issues
    """

    def __init__(self, picture_group, picture):
        """Determines the actual system command to run

        Parameters
        ----------
        picture_group : PictureGroup
            The picture_group to update after the command runs
        picture : Picture
            The picture to delete
        """
        logger.debug(
            f"RemoveProcess.init: {picture_group.trip}/{picture_group.name}/{picture.filename}"
        )
        super().__init__()
        self.signals = ProcessSignals()
        self.picture_group = picture_group

        # Determine the command to run
        self.file = picture.path
        self.location = picture.location

    def run(self):
        """Runs the command, after making sure it won't create issues

        Will emit error signal if target file does not exist or is a folder
        Will emit finished signal once process is complete
        """
        # Check target doesn't exist already
        if not os.path.exists(self.file):
            self.signals.taskError.emit(
                self.picture_group,
                self.location,
                _("The file to delete does not exist"),
            )
            return
        if os.path.isdir(self.file):
            self.signals.taskError.emit(
                self.picture_group,
                self.location,
                _("The element to delete is not a file"),
            )
            return

        try:
            os.unlink(self.file)
            logger.info(
                f"RemoveProcess finished {self.picture_group.trip}/{self.picture_group.name}/{os.path.basename(self.file)}"
            )
            self.signals.taskFinished.emit(
                self.picture_group,
                self.location,
                self.file,
            )
        except Exception as e:
            logger.warning(
                f"RemoveProcess error {self.picture_group.trip}/{self.picture_group.name}/{os.path.basename(self.file)}: {e.args}"
            )
            self.signals.taskError.emit(
                self.picture_group,
                self.location,
                e.args.__repr__(),
            )

    def __repr__(self):
        return "Delete picture: " + self.parameters["command"]


class ChangeTripProcess(QtCore.QRunnable):
    """A process to change the trip of given pictures

    Methods
    -------
    __init__ (picture_group, picture, target_trip)
        Determines the actual system command to run
    run (folders)
        Runs the command, after making sure it won't create issues
    """

    def __init__(self, picture_group, picture, target_trip):
        """Determines the actual system command to run

        Parameters
        ----------
        picture_group : PictureGroup
            The picture_group to update after the command runs
        picture : Picture
            The picture to move
        target_trip : str
            The trip in which to put the picture
        """
        logger.debug(
            f"ChangeTripProcess.init: {picture_group.trip}/{picture_group.name}/{picture.filename} from {picture_group.trip} to {target_trip}"
        )
        super().__init__()
        self.signals = ProcessSignals()
        self.picture_group = picture_group
        self.target_location = picture.location
        self.target_trip = target_trip

        # Determine the command to run
        self.source_file = picture.path

        self.target_folder = os.path.join(
            os.path.dirname(os.path.dirname(picture.path)), target_trip
        )
        self.target_file = os.path.join(self.target_folder, picture.filename)

    def run(self):
        """Runs the command, after making sure it won't create issues

        Will emit error signal if target file already exists
        Will emit finished signal once process is complete
        """
        # Check target doesn't exist already
        if os.path.exists(self.target_file):
            self.signals.taskError.emit(
                self.picture_group,
                self.target_location,
                _("Target file already exists"),
            )
            return
        # Check target folder exists
        if not os.path.exists(self.target_folder):
            os.makedirs(self.target_folder, exist_ok=True)

        try:
            os.rename(self.source_file, self.target_file)
            logger.info(
                f"ChangeTripProcess finished {self.picture_group.trip}/{self.picture_group.name}/{os.path.basename(self.source_file)} from {self.picture_group.trip} to {self.target_trip}"
            )
            self.signals.taskFinished.emit(
                self.picture_group,
                self.target_location,
                self.target_file,
            )
        except Exception as e:
            logger.warning(
                f"ChangeTripProcess error {self.picture_group.trip}/{self.picture_group.name}/{os.path.basename(self.source_file)} from {self.picture_group.trip} to {self.target_trip}: {e.args}"
            )
            self.signals.taskError.emit(
                self.picture_group,
                self.target_location,
                e.args.__repr__(),
            )

    def __repr__(self):
        return "Change trip task: " + self.source_file + " to " + self.target_file


class ProcessSignals(QtCore.QObject):
    """Defines signals when processes are completed or in error

    Attributes
    ----------
    finished : pyqtSignal
        Emitted once a process has finished
    error : pyqtSignal
        Emitted once a process is in error
    """

    taskFinished = QtCore.pyqtSignal(PictureGroup, StorageLocation, str)
    taskError = QtCore.pyqtSignal(PictureGroup, StorageLocation, str)
