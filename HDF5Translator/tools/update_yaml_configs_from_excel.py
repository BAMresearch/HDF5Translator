import subprocess
import os
from pathlib import Path
import attrs
import argparse
import excel_translator

@attrs.define
class Translator:
    input_file: Path = attrs.field()
    output_file: Path = attrs.field(default=None)
    script_path: Path = attrs.field(default=Path('../../src/tools/excel_translator.py'))

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
        """Perform the translation using the external script."""
        try:
            result = subprocess.run(
                ['python', str(self.script_path), '-I', str(self.input_file)],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"Translation completed successfully:\n{result.stdout}")
        except subprocess.CalledProcessError as e:
            print(f"Error during translation:\n{e.stderr}")

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
            translator.translate()
    else:
        print(f"{target} is neither a valid file nor a directory.")

def main():
    parser = argparse.ArgumentParser(description="Check and translate Excel files to YAML if necessary.")
    parser.add_argument("target", help="Directory or file to process.")
    args = parser.parse_args()

    process_directory_or_file(args.target)

if __name__ == "__main__":
    main()