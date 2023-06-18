import os
import shutil
import gettext

from PyQt5 import QtCore
from .picture import Picture as PictureModel
from .picturegroup import PictureGroup

_ = gettext.gettext
# TODO: Repository > add documentation


class Repository:
    allowed_extensions = [".cr2", ".jpg", ".jpeg"]

    def __init__(self, storage_locations=None):
        self.storage_locations = {}
        self.pictures = []
        self.picture_groups = []
        self.process_groups = []

        if storage_locations:
            self.storage_locations = storage_locations.copy()
            self.load_pictures()
        # TODO: Create signals when pictures are added / removed / ...

    def load_pictures(self, storage_locations=None):
        # Find all pictures
        pictures = []
        if storage_locations:
            self.storage_locations |= storage_locations.copy()
            self.pictures = []
            self.picture_groups = []
        for name in self.storage_locations:
            new_pictures = self.read_folder([], name, self.storage_locations[name])
            if new_pictures:
                pictures += new_pictures
        self.pictures = pictures

        # Then group them
        picture_names = set(picture.name for picture in self.pictures)
        picture_names = sorted(picture_names)
        for picture_name in picture_names:
            matching_groups = [
                group
                for group in self.picture_groups
                if picture_name.startswith(group.name)
            ]
            pictures = [
                picture for picture in self.pictures if picture.name == picture_name
            ]

            if len(matching_groups) == 0:
                group = PictureGroup(picture_name)
                self.picture_groups.append(group)
            else:
                # There should not be multiple matching groups
                # This is because groups are created in alphabetical order
                # Therefore groups with shorter names are processed first
                group = matching_groups[0]
            for picture in pictures:
                group.add_picture(picture)

    def read_folder(self, pictures, location_name, path):
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
        picture = PictureModel({location.name: location.path}, path)
        picture_group.add_picture(picture)

    def remove_picture(self, picture_group, picture):
        picture_group.remove_picture(picture)

    def copy_pictures(
        self, target_location, trip=None, picture_group=None, conversion_method=None
    ):
        # Determine all the picture groups to process
        if picture_group:
            picture_groups = [picture_group]
            trip = picture_group.trip
        elif trip:
            picture_groups = self.trips[trip].values()

        if not picture_groups:
            raise ValueError("trip or picture_group is required")

        # Determine the source: if same image exists, then it'll be a copy
        process_group = ProcessGroup("copy", trip, target_location)
        source_pictures = []
        for picture_group in picture_groups:
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
            process = process_group.add_task(source_picture)
            process.signals.finished.connect(
                lambda path: self.add_picture(picture_group, target_location, path)
            )
            QtCore.QThreadPool.globalInstance().start(process, 100)

        self.process_groups.append(process_group)
        return process_group

    def generate_pictures(
        self, target_location, conversion_methods, trip=None, picture_group=None
    ):
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
        source_pictures = []
        for picture_group in picture_groups:
            if "" not in picture_group.pictures:
                raise FileNotFoundError(_("No source image found"))
            source_pictures.append(picture_group.pictures[""][0])

        # Generate tasks for each generation
        for conversion_method in conversion_methods:
            for source_picture in source_pictures:
                process = process_group.add_task(source_picture, conversion_method)
                process.signals.finished.connect(
                    lambda path: self.add_picture(picture_group, target_location, path)
                )
                QtCore.QThreadPool.globalInstance().start(process, 100)

        self.process_groups.append(process_group)
        return process_group

    def __getattr__(self, attr):
        if attr == "trips":
            trips = {}
            for picture_group in self.picture_groups:
                if picture_group.trip not in trips:
                    trips[picture_group.trip] = {}
                trips[picture_group.trip][picture_group.name] = picture_group
            return trips


class ProcessGroup(QtCore.QObject):
    finished = QtCore.pyqtSignal()

    def __init__(self, task_type, trip, target_location):
        super().__init__()
        if task_type not in ["copy", "generate"]:
            raise ValueError("Task type is invalid")
        self.task_type = task_type
        self.trip = trip
        self.progress = 0
        self.tasks = []
        self.target_location = target_location

    def add_task(self, source_picture, method=None):
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
        task["status"] = "Stopped"
        task["file_path"] = path
        self.update_progress()

    def task_error(self, task, error):
        task["status"] = "Stopped"
        task["error"] = error
        self.update_progress()

    def update_progress(self):
        done = len([p for p in self.tasks if p["status"] == "Stopped"])
        self.progress = done / len(self.tasks)
        if done == len(self.tasks):
            self.finished.emit()

    def __repr__(self):
        return (self.task_type, self.trip).__repr__()


class CopyProcess(QtCore.QRunnable):
    def __init__(self, task_group, source_picture):
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

    def run(self):
        # Check target doesn't exist already
        if os.path.exists(self.parameters["target_file"]):
            self.signals.error.emit(_("Target file already exists"))
            return

        # Run the actual processes
        os.makedirs(os.path.dirname(self.parameters["target_file"]), exist_ok=True)
        shutil.copy2(self.parameters["source_file"], self.parameters["target_file"])
        self.signals.finished.emit(self.parameters["target_file"])


class GenerateProcess(QtCore.QRunnable):
    def __init__(self, task_group, source_picture, method):
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
        # Check target doesn't exist already
        if os.path.exists(self.parameters["target_file"]):
            self.signals.error.emit(_("Target file already exists"))
            return

        os.system(self.parameters["command"])
        self.signals.finished.emit(self.parameters["target_file"])


class ProcessSignals(QtCore.QObject):
    finished = QtCore.pyqtSignal(str)
    error = QtCore.pyqtSignal(str)
