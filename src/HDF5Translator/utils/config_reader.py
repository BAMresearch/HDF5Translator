import yaml
from typing import List
from ..translator_elements import TranslationElement

def read_translation_config(filepath: str) -> List[TranslationElement]:
    with open(filepath, 'r') as file:
        config = yaml.safe_load(file)
    translations = [TranslationElement(**item) for item in config['translations']]
    return translations

# Example usage
if __name__ == "__main__":
    config_path = '../defaults/example_translation_config.yaml'
    translations = read_translation_config(config_path)
    for translation in translations:
        print(translation)