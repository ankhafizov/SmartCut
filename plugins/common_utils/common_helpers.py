import yaml


def read_config(path: str) -> dict:
    with open(path, "r") as f:
        config = yaml.safe_load(f)

    return config
