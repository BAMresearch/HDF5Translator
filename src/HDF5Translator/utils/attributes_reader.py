import yaml

def read_attributes_from_yaml(config_path: str):
    """
    Reads attribute configurations from a YAML file.

    Args:
        config_path (str): Path to the YAML configuration file.

    Returns:
        dict: A dictionary containing the attribute configurations.
    """
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config.get('attributes', {})