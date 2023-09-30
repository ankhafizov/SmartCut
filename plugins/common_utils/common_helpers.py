import yaml
import shutil
import os.path

import logging


def read_config(path: str) -> dict:
    with open(path, "r") as f:
        config = yaml.safe_load(f)

    return config


def unzip_archive(path_to_archive: str) -> str:
    assert path_to_archive[-4:] == ".zip"
    assert os.path.isfile(path_to_archive)
    path_to_unpacked_content = path_to_archive[:-4]
    shutil.unpack_archive(path_to_archive, path_to_unpacked_content)
    logging.info(f"unpacked archive {path_to_archive} to {path_to_unpacked_content}")

    return path_to_unpacked_content
