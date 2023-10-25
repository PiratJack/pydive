import os
import shutil
import sys
import pytest
import datetime
import logging
import zipfile

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "pydive"))


import models.database
import models.repository

import controllers.mainwindow

from models.storagelocation import StorageLocation
from models.storagelocation import StorageLocationType
from models.conversionmethod import ConversionMethod
from models.category import Category
from models.divelog import DiveLog

logging.basicConfig(level=logging.CRITICAL)


def pytest_configure():
    pytest.DATABASE_FILE = "test.sqlite"
    pytest.BASE_FOLDER = (
        "./test_images" + str(int(datetime.datetime.now().timestamp())) + "/"
    )
    pytest.PICTURE_ZIP_FILE = os.path.join(BASE_DIR, "test_photos.zip")
    pytest.DIVELOG_ZIP_FILE = os.path.join(BASE_DIR, "test_divelog.zip")
    pytest.DIVELOG_FILE = os.path.join(pytest.BASE_FOLDER, "test_divelog.xml")
    pytest.DIVELOG_SCAN_IMAGE = os.path.join(pytest.BASE_FOLDER, "Divelog scan.jpg")


@pytest.fixture
def pydive_db():
    try:
        os.remove(pytest.DATABASE_FILE)
    except OSError:
        pass
    database = models.database.Database(pytest.DATABASE_FILE)
    database.session.add_all(
        [
            # Test with final "/" in path
            StorageLocation(
                id=1,
                name="Camera",
                type="picture_folder",
                path=os.path.join(pytest.BASE_FOLDER, "DCIM", ""),
            ),
            # Test without final "/" in path
            StorageLocation(
                id=2,
                name="Temporary",
                type="picture_folder",
                path=os.path.join(pytest.BASE_FOLDER, "Temporary"),
            ),
            StorageLocation(
                id=3,
                name="Archive",
                type=StorageLocationType["picture_folder"],
                path=os.path.join(pytest.BASE_FOLDER, "Archive"),
            ),
            StorageLocation(
                id=4,
                name="Inexistant",
                type="picture_folder",
                path=os.path.join(pytest.BASE_FOLDER, "Inexistant"),
            ),
            StorageLocation(
                id=5,
                name="No picture here",
                type="picture_folder",
                path=os.path.join(pytest.BASE_FOLDER, "Empty"),
            ),
            StorageLocation(
                id=6,
                name="Dive log",
                type="file",
                path=pytest.DIVELOG_FILE,
            ),
            StorageLocation(
                id=7,
                name="Scan split folder",
                type="target_scan_folder",
                path=pytest.BASE_FOLDER,
            ),
            ConversionMethod(
                id=1,
                name="DarkTherapee",
                suffix="DT",
                command="cp %SOURCE_FILE% %TARGET_FILE%",
            ),
            ConversionMethod(
                id=2,
                name="RawTherapee",
                suffix="RT",
                command="cp %SOURCE_FILE% %TARGET_FILE%",
            ),
            Category(
                id=1,
                name="Top",
                path="Sélection",
            ),
            Category(
                id=2,
                name="Bof",
                path="Bof",
            ),
        ]
    )
    database.session.commit()
    database.session.close()
    database.engine.dispose()

    yield database

    # Delete database
    os.remove(pytest.DATABASE_FILE)


@pytest.fixture
def pydive_repository(pydive_db):
    repository = models.repository.Repository(pydive_db)
    repository.load_pictures()
    yield repository


@pytest.fixture
def pydive_fake_pictures():
    try:
        shutil.rmtree(pytest.BASE_FOLDER)
    except OSError:
        pass

    all_folders = [
        ".",
        os.path.join("DCIM", ""),
        os.path.join("DCIM", "Sweden", ""),
        os.path.join("Temporary", ""),
        os.path.join("Temporary", "Malta", ""),
        os.path.join("Temporary", "Malta", "Sélection", ""),
        os.path.join("Temporary", "Malta", "Unknown_category", ""),
        os.path.join("Temporary", "Georgia", ""),
        os.path.join("Temporary", "Korea", ""),
        os.path.join("Temporary", "Sweden", ""),
        os.path.join("Archive", ""),
        os.path.join("Archive", "Malta", ""),
        os.path.join("Archive", "Korea", ""),
        os.path.join("Archive", "Sweden", ""),
        os.path.join("Archive", "Romania", ""),
        os.path.join("Archive", "Island", ""),
        os.path.join("Archive_outside_DB", ""),
        os.path.join("Archive_outside_DB", "Egypt", ""),
        os.path.join("Empty", ""),
    ]
    for folder in all_folders:
        os.makedirs(os.path.join(pytest.BASE_FOLDER, folder), exist_ok=True)

    all_files = [
        os.path.join("DCIM", "IMG001.CR2"),
        os.path.join("DCIM", "IMG002.CR2"),
        os.path.join("DCIM", "IMG010.CR2"),
        os.path.join("DCIM", "IMG020.CR2"),
        os.path.join("Temporary", "Malta", "IMG001.CR2"),
        os.path.join("Temporary", "Malta", "IMG001_RT.jpg"),
        os.path.join("Temporary", "Malta", "Sélection", "IMG001_RT.jpg"),
        os.path.join("Temporary", "Malta", "Unknown_category", "IMG001_RT.jpg"),
        os.path.join("Temporary", "Malta", "IMG002.CR2"),
        os.path.join("Temporary", "Malta", "IMG002_RT.jpg"),
        os.path.join("Archive", "Malta", "IMG001.CR2"),
        os.path.join("Archive", "Malta", "IMG002.CR2"),
        os.path.join("Temporary", "Georgia", "IMG010.CR2"),
        os.path.join("Temporary", "Georgia", "IMG010_RT.jpg"),
        os.path.join("Temporary", "Georgia", "IMG011_convert.jpg"),
        os.path.join("Temporary", "Korea", "IMG030.CR2"),
        os.path.join("Archive", "Korea", "IMG030_RT.jpg"),
        os.path.join("Temporary", "Sweden", "IMG040.CR2"),
        os.path.join("Temporary", "Sweden", "IMG041.CR2"),
        os.path.join("Temporary", "Sweden", "IMG040_RT.jpg"),
        os.path.join("Temporary", "Sweden", "IMG040_DT.jpg"),
        os.path.join("Archive", "Sweden", "IMG040_convert.jpg"),
        os.path.join("Archive", "Romania", "IMG050.CR2"),
        os.path.join("Archive", "Romania", "IMG050_convert.jpg"),
        os.path.join("Archive", "Island", "IMG050.CR2"),
        os.path.join("Archive_outside_DB", "Egypt", "IMG037.CR2"),
    ]
    for test_file in all_files:
        open(os.path.join(pytest.BASE_FOLDER, test_file), "w").close()

    yield all_files

    # Delete folders
    shutil.rmtree(pytest.BASE_FOLDER)


@pytest.fixture
def pydive_real_pictures():
    try:
        shutil.rmtree(pytest.BASE_FOLDER)
    except OSError:
        pass

    all_files = [
        os.path.join("DCIM", "IMG050.CR2"),
        os.path.join("DCIM", "122_12", "IMG001.CR2"),
        os.path.join("DCIM", "122_12", "IMG002.CR2"),
        os.path.join("DCIM", "123__05", "IMG010.CR2"),
        os.path.join("DCIM", "123__05", "IMG020.CR2"),
        os.path.join("Temporary", "Georgia", "IMG010.CR2"),
        os.path.join("Temporary", "Georgia", "IMG010_RT.jpg"),
        os.path.join("Temporary", "Georgia", "IMG011_convert.jpg"),
        os.path.join("Temporary", "Korea", "IMG030.CR2"),
        os.path.join("Archive", "Korea", "IMG030_RT.jpg"),
        os.path.join("Temporary", "Malta", "IMG001.CR2"),
        os.path.join("Temporary", "Malta", "IMG001_RT.jpg"),
        os.path.join("Temporary", "Malta", "IMG002.CR2"),
        os.path.join("Temporary", "Malta", "IMG002_RT.jpg"),
        os.path.join("Archive", "Malta", "IMG001.CR2"),
        os.path.join("Archive", "Malta", "Bof", "IMG001.CR2"),
        os.path.join("Archive", "Malta", "IMG002.CR2"),
        os.path.join("Archive", "Malta", "Sélection", "IMG002.CR2"),
        os.path.join("Temporary", "Sweden", "IMG040.CR2"),
        os.path.join("Temporary", "Sweden", "IMG041.CR2"),
        os.path.join("Temporary", "Sweden", "IMG040_RT.jpg"),
        os.path.join("Temporary", "Sweden", "IMG040_DT.jpg"),
        os.path.join("Archive", "Sweden", "IMG040_convert.jpg"),
        os.path.join("Archive_outside_DB", "Egypt", "IMG037.CR2"),
    ]
    with zipfile.ZipFile(pytest.PICTURE_ZIP_FILE, "r") as zip_ref:
        zip_ref.extractall(".")
        os.rename("test_photos", pytest.BASE_FOLDER)

    yield all_files

    # Delete folders
    shutil.rmtree(pytest.BASE_FOLDER)


@pytest.fixture
# qtbot is here to make sure we have a QApplication running
def pydive_mainwindow(qtbot, pydive_db):
    repository = models.repository.Repository(pydive_db)
    mainwindow = controllers.mainwindow.MainWindow(pydive_db, repository)

    yield mainwindow

    mainwindow.database.session.close()
    mainwindow.database.engine.dispose()


@pytest.fixture
def pydive_divelog(qtbot, pydive_db):
    os.makedirs(pytest.BASE_FOLDER, exist_ok=True)
    all_files = [
        os.path.join(pytest.BASE_FOLDER, "Divelog raw image.jpg"),
        os.path.join(pytest.BASE_FOLDER, "test_divelog.xml"),
    ]
    with zipfile.ZipFile(pytest.DIVELOG_ZIP_FILE, "r") as zip_ref:
        zip_ref.extractall(".")
        os.rename("test_divelog", pytest.BASE_FOLDER)

    divelog = DiveLog(pytest.DIVELOG_FILE)

    yield divelog

    shutil.rmtree(pytest.BASE_FOLDER)
