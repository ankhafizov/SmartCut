import yaml
import shutil


def read_config(path: str) -> dict:
    with open(path, "r") as f:
        config = yaml.safe_load(f)

    return config


def unzip_archive(path_to_archive: str) -> str:
    assert path_to_archive[-4:] == ".zip"
    path_to_unpacked_content = path_to_archive[:-4]
    shutil.unpack_archive(path_to_archive, path_to_unpacked_content)

    return path_to_unpacked_content
