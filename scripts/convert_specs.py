import yaml
import re
from pathlib import Path


def convert_spec(input_path: Path, output_path: Path):
    """Convert space-aligned spec to structured YAML"""
    specs = {}

    with open(input_path) as f:
        # Skip header line
        next(f)

        for line in f:
            # Split on 2+ spaces to handle aligned columns
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) != 6:
                continue

            iform = parts[3]
            specs[iform] = {
                'iclass': parts[0],
                'extension': parts[1],
                'category': parts[2],
                'isa_set': parts[4],
                'attributes': parts[5].split()
            }

    with open(output_path, 'w') as f:
        yaml.safe_dump(specs, f, default_flow_style=False, sort_keys=False)


if __name__ == '__main__':
    input_file = Path('config/instruction_specs/x86_64.spec')
    output_file = Path('config/instruction_specs/x86_64.yaml')

    convert_spec(input_file, output_file)
    print(f"Converted {input_file} to {output_file}")
