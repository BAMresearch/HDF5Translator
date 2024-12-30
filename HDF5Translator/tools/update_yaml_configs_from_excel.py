import argparse
import os
from pathlib import Path

import attrs
from excel_translator import excel_translator


@attrs.define
class Translator:
    input_file: Path = attrs.field()
    output_file: Path = attrs.field(default=None)

    def __attrs_post_init__(self):
        # Set default output extension if not provided
        if self.output_file is None:
            self.output_file = self.input_file.with_suffix('.yaml')

    def is_update_needed(self):
        """Check if the Excel file is newer than the YAML file."""
        if not self.output_file.exists():
            return True
        
        return self.input_file.stat().st_mtime > self.output_file.stat().st_mtime

    def translate(self):
        """Perform the translation using the directly imported function."""
        try:
            excel_translator(self.input_file, self.output_file)
            print(f"Translation completed successfully for: {self.input_file}")
        except Exception as e:
            print(f"Error during translation for {self.input_file}: {e}")

def process_directory_or_file(target):
    target = Path(target)

    if target.is_dir():
        for excel_file in target.glob('*.xlsx'):
            yaml_file = excel_file.with_suffix('.yaml')
            translator = Translator(input_file=excel_file, output_file=yaml_file)
            if translator.is_update_needed():
                translator.translate()
    elif target.is_file():
        yaml_file = target.with_suffix('.yaml')
        translator = Translator(input_file=target, output_file=yaml_file)
        if translator.is_update_needed():
            print(f"Translating {target} to {yaml_file}")
            translator.translate()
        else: 
            print(f"No translation needed for {target}, {yaml_file} is up to date.")
    else:
        print(f"{target} is neither a valid file nor a directory.")

def main():
    parser = argparse.ArgumentParser(description="Check and translate Excel files to YAML if necessary.")
    parser.add_argument("target", help="Directory or file to process.")
    args = parser.parse_args()

    process_directory_or_file(args.target)

if __name__ == "__main__":
    main()