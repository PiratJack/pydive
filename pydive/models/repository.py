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

ProcessSignals
    Defines signals when processes are completed or in error
"""
import os
import shutil
import gettext

from PyQt5 import QtCore
from .picture import Picture as PictureModel
from .picturegroup import PictureGroup

_ = gettext.gettext


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
    remove_picture (picture_group, picture)
        Removes (deletes) a single picture
    copy_pictures (target_location, trip, picture_group, conversion_method)
        Copies pictures between folders
    generate_pictures (target_location, conversion_methods, trip, picture_group)
        Generates pictures by converting between different formats

    """

    allowed_extensions = [".cr2", ".jpg", ".jpeg"]

    def __init__(self):
        """Defines default attributes"""
        self.storage_locations = {}
        self.picture_groups = []
        self.process_groups = []
        # TODO: Darktherapee prevents multithreading, hence this (ugly) workaround
        QtCore.QThreadPool.globalInstance().setMaxThreadCount(1)

    def load_pictures(self, storage_locations):
        """Loads all pictures from the provided storage locations (folders)

        Pictures are added in the corresponding picture_group

        Parameters
        ----------
        storage_locations : dict of str
            The storage locations, in form name:path
        """
        # Find all pictures
        pictures = []
        self.storage_locations |= storage_locations.copy()
        self.picture_groups = []
        for name in self.storage_locations:
            new_pictures = self.read_folder([], name, self.storage_locations[name])
            if new_pictures:
                pictures += new_pictures

        # Then group them
        picture_names = set(picture.name for picture in pictures)
        picture_names = sorted(picture_names)
        for picture_name in picture_names:
            matching_groups = [
                group
                for group in self.picture_groups
                if picture_name.startswith(group.name)
            ]
            matching_pictures = [
                picture for picture in pictures if picture.name == picture_name
            ]

            if len(matching_groups) == 0:
                group = PictureGroup(picture_name)
                self.picture_groups.append(group)
            else:
                # There should not be multiple matching groups
                # This is because groups are created in alphabetical order
                # Therefore groups with shorter names are processed first
                group = matching_groups[0]
            for picture in matching_pictures:
                group.add_picture(picture)

    def read_folder(self, pictures, location_name, path):
        """Reads a given folder recursively to find pictures

        Parameters
        ----------
        pictures : list of Picture
            The list in which to add new pictures
        location_name : str
            The name of the storage location
        path : str
            The path to explore (will do nothing if it's not a folder)
        """
        if not os.path.isdir(path):
            return None
        for element in os.listdir(path):
            full_path = os.path.join(path, element)
            if os.path.isdir(full_path):
                self.read_folder(pictures, location_name, full_path)
            else:
                matching_extension = [
                    ext
                    for ext in self.allowed_extensions
                    if full_path.lower().endswith(ext)
                ]
                if matching_extension:
                    pictures.append(PictureModel(self.storage_locations, full_path))
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
        picture = PictureModel({location.name: location.path}, path)
        picture_group.add_picture(picture)

    def remove_picture(self, picture_group, picture):
        """Removes (deletes) a single picture

        Parameters
        ----------
        picture_group : PictureGroup
            The picture group in which to add the picture
        picture : Picture
            The picture to delete
        """
        picture_group.remove_picture(picture)

    def copy_pictures(
        self,
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
        # Determine all the picture groups to process
        picture_groups = None
        if picture_group:
            picture_groups = [picture_group]
            trip = picture_group.trip
        elif trip:
            picture_groups = self.trips[trip].values()

        if not picture_groups:
            raise ValueError("trip or picture_group is required")

        # Determine the source: if same image exists, then it'll be a copy
        process_group = ProcessGroup("copy", trip, target_location)
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
                    and source_picture.location_name != source_location.name
                ):
                    continue
                process = process_group.add_task(source_picture)
                # TODO: Processes > simplify by putting all parameters in the signal
                process.signals.finished.connect(
                    lambda path, picture_group=picture_group, target_location=target_location: self.add_picture(
                        picture_group, target_location, path
                    )
                )
                QtCore.QThreadPool.globalInstance().start(process, 100)

        self.process_groups.append(process_group)
        return process_group

    def generate_pictures(
        self,
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
        target_location : StorageLocation
            The location in which pictures should be copied
        conversion_methods : ConversionMethod
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
        if picture_group:
            picture_groups = [picture_group]
            trip = picture_group.trip
        elif trip:
            picture_groups = self.trips[trip].values()

        if not picture_groups:
            raise ValueError("trip or picture_group is required")

        # Determine the source: find the RAW image
        process_group = ProcessGroup("generate", trip, target_location)
        for picture_group in picture_groups:
            source_pictures = []
            if "" not in picture_group.pictures:
                raise FileNotFoundError(_("No source image found"))
            source_pictures.append(picture_group.pictures[""][0])

            # Generate tasks for each generation
            for conversion_method in conversion_methods:
                for source_picture in source_pictures:
                    if (
                        source_location
                        and source_picture.location_name != source_location.name
                    ):
                        continue
                    process = process_group.add_task(source_picture, conversion_method)
                    # TODO: Processes > simplify by putting all parameters in the signal
                    process.signals.finished.connect(
                        lambda path, picture_group=picture_group, target_location=target_location: self.add_picture(
                            picture_group, target_location, path
                        )
                    )
                    QtCore.QThreadPool.globalInstance().start(process, 100)

        self.process_groups.append(process_group)
        return process_group

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
    __init__ (task_type, trip, target_location)
        Stores basic information about the task group
    add_task (source_picture, method)
        Adds a new task to the group
    task_done (task, path)
        Marks a single task as in done & stopped. Triggers self.update_progress
    task_error (task, error)
        Marks a single task as in error & stopped. Triggers self.update_progress
    update_progress
        Updates the progress. Emits finishes signal once complete.
    """

    finished = QtCore.pyqtSignal()

    def __init__(self, task_type, trip, target_location):
        """Stores basic information about the task group

        Parameters
        ----------
        task_type : "copy" or "generate"
            Which task to perform
        trip : str
            The name of the trip of the picture to copy/generate
        target_location : StorageLocation
            The location in which to copy or generate
        """
        super().__init__()
        if task_type not in ["copy", "generate"]:
            raise ValueError("Task type is invalid")
        self.task_type = task_type
        self.trip = trip
        self.progress = 0
        self.tasks = []
        self.target_location = target_location

    def add_task(self, source_picture, method=None):
        """Adds a new task to the group

        Parameters
        ----------
        source_picture : Picture
            The picture to copy or convert
        method : ConversionMethod
            The method to use for conversion. None for copies.
        """
        if self.task_type == "copy":
            process = CopyProcess(self, source_picture)
        elif self.task_type == "generate":
            process = GenerateProcess(self, source_picture, method)
        task = {"source_picture": source_picture, "status": "Queued"}
        self.tasks.append(task)
        process.signals.finished.connect(
            lambda path, task=task: self.task_done(task, path)
        )
        process.signals.error.connect(
            lambda error, task=task: self.task_error(task, error)
        )
        return process

    def task_done(self, task, path):
        """Marks a single task as in done & stopped. Triggers self.update_progress

        Parameters
        ----------
        task : CopyProcess or GenerateProcess
            The task in error
        path : str
            The path of the newly created image
        """
        task["status"] = "Stopped"
        task["file_path"] = path
        self.update_progress()

    def task_error(self, task, error):
        """Marks a single task as in error & stopped. Triggers self.update_progress

        Parameters
        ----------
        task : CopyProcess or GenerateProcess
            The task in error
        error : str
            The error message
        """
        task["status"] = "Stopped"
        task["error"] = error
        self.update_progress()

    def update_progress(self):
        """Updates the progress. Emits finishes signal once complete."""
        done = len([p for p in self.tasks if p["status"] == "Stopped"])
        self.progress = done / len(self.tasks)
        if done == len(self.tasks):
            self.finished.emit()

    def __repr__(self):
        return (self.task_type, self.trip).__repr__()


class CopyProcess(QtCore.QRunnable):
    """A process to copy pictures between locations

    Methods
    -------
    __init__ (task_group, source_picture)
        Stores the required parameters for the copy
    run (folders)
        Runs the copy, after making sure it won't create issues
    """

    def __init__(self, task_group, source_picture):
        """Stores the required parameters for the copy

        Parameters
        ----------
        task_group : ProcessGroup
            The group of related task this belongs to
        source_picture : Picture
            The source picture to copy
        """
        super().__init__()
        self.signals = ProcessSignals()

        # Determine picture's target path
        target_path = os.path.join(
            task_group.target_location.path,
            task_group.trip,
            os.path.basename(source_picture.path),
        )
        # Store all parameters
        self.parameters = {
            "source_file": source_picture.path,
            "target_file": target_path,
        }

    def __repr__(self):
        return "Copy task: " + self.parameters.__repr__()

    def run(self):
        """Runs the copy, after making sure it won't create issues

        Will emit error signal if target file already exists
        Will emit finished signal once copy is complete
        """
        # Check target doesn't exist already
        if os.path.exists(self.parameters["target_file"]):
            self.signals.error.emit(_("Target file already exists"))
            return

        # Run the actual processes
        os.makedirs(os.path.dirname(self.parameters["target_file"]), exist_ok=True)
        shutil.copy2(self.parameters["source_file"], self.parameters["target_file"])
        self.signals.finished.emit(self.parameters["target_file"])


class GenerateProcess(QtCore.QRunnable):
    """A process to generate pictures from raw pictures

    Methods
    -------
    __init__ (task_group, source_picture, method)
        Determines the actual system command to run
    run (folders)
        Runs the command, after making sure it won't create issues
    """

    def __init__(self, task_group, source_picture, method):
        """Determines the actual system command to run

        Parameters
        ----------
        task_group : ProcessGroup
            The group of related task this belongs to
        source_picture : Picture
            The RAW picture to convert
        method : ConversionMethod
            The method to convert the image
        """
        super().__init__()
        self.signals = ProcessSignals()

        # Determine the command to run
        parameters = {
            "command": "",
            "source_file": "",
            "target_folder": "",
            "target_file": "",
        }

        parameters["target_folder"] = os.path.join(
            task_group.target_location.path, task_group.trip
        )

        parameters["source_file"] = source_picture.path

        target_file_name = source_picture.name + "_" + method.suffix + ".jpg"
        target_file = os.path.join(parameters["target_folder"], target_file_name)
        parameters["target_file"] = target_file

        # Let's mix all that together!
        command = method.command
        command = command.replace("%SOURCE_FILE%", parameters["source_file"])
        command = command.replace("%TARGET_FILE%", parameters["target_file"])
        command = command.replace("%TARGET_FOLDER%", parameters["target_folder"])
        parameters["command"] = command

        self.parameters = parameters

    def run(self):
        """Runs the command, after making sure it won't create issues

        Will emit error signal if target file already exists
        Will emit finished signal once process is complete
        """
        # Check target doesn't exist already
        if os.path.exists(self.parameters["target_file"]):
            self.signals.error.emit(_("Target file already exists"))
            return
        # Check target folder exists
        if not os.path.exists(self.parameters["target_folder"]):
            os.makedirs(self.parameters["target_folder"], exist_ok=True)

        os.system(self.parameters["command"])
        self.signals.finished.emit(self.parameters["target_file"])

    def __repr__(self):
        return "Generate task: " + self.parameters["command"]


class ProcessSignals(QtCore.QObject):
    """Defines signals when processes are completed or in error

    Attributes
    ----------
    finished : pyqtSignal
        Emitted once a process has finished
    error : pyqtSignal
        Emitted once a process is in error
    """

    finished = QtCore.pyqtSignal(str)
    error = QtCore.pyqtSignal(str)
