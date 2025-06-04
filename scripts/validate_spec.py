import yaml
import sys


def validate_spec(path: str):
    with open(path) as f:
        try:
            data = yaml.safe_load(f)
            if not isinstance(data, dict):
                raise ValueError("Root element must be a dictionary")
            print(f"Valid spec with {len(data)} instructions")
        except Exception as e:
            print(f"Invalid spec: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    validate_spec(sys.argv[1])
