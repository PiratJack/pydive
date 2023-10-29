"""Background processes to run for file changes

Classes
----------
ProcessScaffold
    The base class for the *Process classes

CopyProcess
    A process to copy pictures from one location to another

GenerateProcess
    A process to generate pictures from raw pictures

RemoveProcess
    A process to delete pictures

ChangeTripProcess
    A process to change the trip of given pictures

ProcessSignals
    Defines signals when processes are completed or in error
"""
import os
import shlex
import shutil
import gettext
import logging

from PyQt5 import QtCore
from .picturegroup import PictureGroup
from .storagelocation import StorageLocation

_ = gettext.gettext
logger = logging.getLogger(__name__)


class ProcessScaffold:
    def cancel(self):
        if self.status == "Queued":
            self.status = "Cancelled"
            self.signals.taskError.emit(
                _("Task cancelled"),
                _("Task cancelled {short_path} - {target_file}").format(
                    short_path=self.short_path, target_file=self.target_file
                ),
            )


class CopyProcess(QtCore.QRunnable, ProcessScaffold):
    """A process to copy pictures between locations

    Methods
    -------
    __init__ (picture_group, source_picture, target_location)
        Stores the required parameters for the copy
    run
        Runs the copy, after making sure it won't create issues
    """

    def __init__(
        self, picture_group, source_picture, target_location, target_category=None
    ):
        """Stores the required parameters for the copy

        Parameters
        ----------
        picture_group : PictureGroup
            The group of pictures to copy
        source_picture : Picture
            The source picture to copy
        target_location : StorageLocation
            The location where to copy the picture
        target_category : models.category.Category
            The category in which to copy the picture
        """
        logger.debug(
            f"CopyProcess.init {picture_group.trip}/{picture_group.name}/{target_category.relative_path+'/' if target_category else ''}{source_picture.filename} to {target_location.name}"
        )
        super().__init__()
        self.status = "Queued"
        self.signals = ProcessSignals()
        self.picture_group = picture_group
        self.source_picture = source_picture
        self.target_location = target_location
        self.target_category = target_category

        self.source_file = source_picture.path
        # Determine picture's target path
        if self.target_category:
            self.target_file = os.path.join(
                target_location.path,
                source_picture.trip,
                self.target_category.relative_path,
                source_picture.filename,
            )
        else:
            self.target_file = os.path.join(
                target_location.path,
                source_picture.trip,
                source_picture.filename,
            )

        self.short_path = self.target_file.replace(
            target_location.path, "[" + target_location.name + "]" + os.path.sep
        )

    def run(self):
        """Runs the copy, after making sure it won't create issues

        Will emit error signal if target file already exists
        Will emit finished signal once copy is complete
        """
        # Check target doesn't exist already
        logger.debug(f"CopyProcess.run {self.source_file} to {self.target_file}")
        if self.status == "Cancelled":
            return
        self.status = "Running"
        if os.path.exists(self.target_file):
            logger.warning(
                f"CopyProcess error {self.picture_group.trip}/{self.picture_group.name}/{os.path.basename(self.source_file)} to {self.target_location.name} - Target file exists"
            )
            self.signals.taskError.emit(
                _("Target file already exists"),
                _("Target file already exists: {short_path} - {target_file}").format(
                    short_path=self.short_path, target_file=self.target_file
                ),
            )
            return

        # Check source file exists
        if not os.path.exists(self.source_file):
            logger.warning(
                f"CopyProcess error {self.picture_group.trip}/{self.picture_group.name}/{os.path.basename(self.source_file)} to {self.target_location.name} - Source file missing"
            )
            self.signals.taskError.emit(
                _("Source file does not exists"),
                _("Source file does not exists: {short_path} - {source_file}").format(
                    short_path=self.short_path, source_file=self.source_file
                ),
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

    def __repr__(self):
        return f"Copy picture: {self.source_file} to {self.target_file}"


class GenerateProcess(QtCore.QRunnable, ProcessScaffold):
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
        self.status = "Queued"
        self.signals = ProcessSignals()
        self.picture_group = picture_group
        self.location = location

        # Determine folder / file paths
        self.source_file = source_picture.path

        self.target_folder = os.path.join(location.path, picture_group.trip)
        target_file_name = source_picture.name + "_" + method.suffix + ".jpg"
        self.target_file = os.path.join(self.target_folder, target_file_name)

        self.short_path = self.target_file.replace(
            self.location.path, "[" + self.location.name + "]" + os.path.sep
        )

        # Let's mix all that together!
        command = method.command
        command = command.replace("%SOURCE_FILE%", shlex.quote(self.source_file))
        command = command.replace("%TARGET_FILE%", shlex.quote(self.target_file))
        command = command.replace("%TARGET_FOLDER%", shlex.quote(self.target_folder))
        self.command = command

    def run(self):
        """Runs the command, after making sure it won't create issues

        Will emit error signal if target file already exists
        Will emit finished signal once process is complete
        """
        # Check target doesn't exist already
        logger.debug(
            f"GenerateProcess.run {self.picture_group.trip}/{self.picture_group.name}/{os.path.basename(self.source_file)} to {self.location.name}..{os.path.basename(self.target_file)}"
        )
        if self.status == "Cancelled":
            return
        self.status = "Running"
        if os.path.exists(self.target_file):
            logger.warning(
                f"GenerateProcess error {self.picture_group.trip}/{self.picture_group.name}/{os.path.basename(self.source_file)} to {self.location.name} - Target file exists"
            )
            self.signals.taskError.emit(
                _("Target file already exists"),
                _("Target file already exists: {short_path} - {target_file}").format(
                    short_path=self.short_path, target_file=self.target_file
                ),
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
        return f"Generate picture: {self.command}"


class RemoveProcess(QtCore.QRunnable, ProcessScaffold):
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
        self.status = "Queued"
        self.signals = ProcessSignals()
        self.picture_group = picture_group
        self.source_picture = picture

        # Determine the command to run
        self.file = picture.path
        self.location = picture.location

        self.short_path = self.file.replace(
            self.location.path, "[" + self.location.name + "]" + os.path.sep
        )

    def run(self):
        """Runs the command, after making sure it won't create issues

        Will emit error signal if target file does not exist or is a folder
        Will emit finished signal once process is complete
        """
        # Check target doesn't exist already
        logger.debug(f"RemoveProcess.run {self.file}")
        if self.status == "Cancelled":
            return
        self.status = "Running"
        if not os.path.exists(self.file):
            logger.warning(
                f"RemoveProcess error {self.picture_group.trip}/{self.picture_group.name}/{os.path.basename(self.file)}: File does not exist"
            )
            self.signals.taskError.emit(
                _("The file to delete does not exist"),
                _("The file to delete does not exist: {short_path} - {path}").format(
                    short_path=self.short_path, path=self.file
                ),
            )

            return
        if os.path.isdir(self.file):
            logger.warning(
                f"RemoveProcess error {self.picture_group.trip}/{self.picture_group.name}/{os.path.basename(self.file)}: Element to delete is not a file"
            )
            self.signals.taskError.emit(
                _("The element to delete is not a file"),
                _("The element to delete is not a file: {short_path} - {path}").format(
                    short_path=self.short_path, path=self.file
                ),
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
                e.args.__repr__(),
                _("{error}: {short_path} - {path}").format(
                    error=e.args.__repr__(),
                    short_path=self.short_path,
                    path=self.source_file,
                ),
            )

    def __repr__(self):
        return f"Delete picture: {self.file}"


class ChangeTripProcess(QtCore.QRunnable, ProcessScaffold):
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
        self.status = "Queued"
        self.signals = ProcessSignals()
        self.picture_group = picture_group
        self.source_picture = picture
        self.target_location = picture.location
        self.target_trip = target_trip

        # Determine the command to run
        self.source_file = picture.path

        self.target_folder = os.path.join(
            picture.location.path,
            target_trip,
            picture.category.relative_path if picture.category else "",
        )
        self.target_file = os.path.join(self.target_folder, picture.filename)

        self.short_path = self.source_file.replace(
            picture.location.path, "[" + picture.location.name + "]" + os.path.sep
        )

    def run(self):
        """Runs the command, after making sure it won't create issues

        Will emit error signal if target file already exists
        Will emit finished signal once process is complete
        """
        logger.debug(
            f"ChangeTripProcess.run {self.picture_group.trip}/{self.picture_group.name}/{os.path.basename(self.source_file)} from {self.picture_group.trip} to {self.target_trip}"
        )
        if self.status == "Cancelled":
            return
        self.status = "Running"
        # Check target doesn't exist already
        if os.path.exists(self.target_file):
            logger.warning(
                f"ChangeTripProcess error {self.picture_group.trip}/{self.picture_group.name}/{os.path.basename(self.source_file)} from {self.picture_group.trip} to {self.target_trip}: Target file exists"
            )
            self.signals.taskError.emit(
                _("Target file already exists"),
                _("Target file already exists: {short_path} - {target_file}").format(
                    short_path=self.short_path, target_file=self.target_file
                ),
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
                e.args.__repr__(),
                _("{error}: {short_path} to {target_trip} - {source_file}").format(
                    error=e.args.__repr__(),
                    short_path=self.short_path,
                    target_trip=self.target_trip,
                    source_file=self.source_file,
                ),
            )

    def __repr__(self):
        return f"Change trip: {self.source_file} to {self.target_file}"


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
    taskError = QtCore.pyqtSignal(str, str)
