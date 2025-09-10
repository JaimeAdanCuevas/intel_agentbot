import os
import re
import requests
import csv
import subprocess
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Configuration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
MODEL_NAME = "gpt-4o"
BASE_URL = "https://apis-internal.intel.com/generativeaiinference/v4"
AUTH_URL = "https://apis-internal.intel.com/v1/auth/token"
LOG_FILE = "tests/integration/data/stress-ng-cpu-mix-out.log"
COVERAGE_CSV = "tests/integration/data/coverage_report.csv"
SDE_OUTPUT = "tests/integration/data/stress-ng-cpu-mix-out.txt"
OUTPUT_SUGGESTIONS = "tests/integration/data/coverage_suggestions.txt"
SPEC_FILE = "config/instruction_specs/x86_64.yaml"

# Set proxies
os.environ['http_proxy'] = 'http://proxy-dmz.intel.com:912'
os.environ['https_proxy'] = 'http://proxy-dmz.intel.com:912'


def get_access_token():
    """Obtain access token from Intel's auth API."""
    resp = requests.post(AUTH_URL, data={
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    })
    if resp.status_code != 200:
        raise Exception(f"Token request failed: {resp.status_code} {resp.text}")
    return resp.json()['access_token']


def create_llm():
    """Create LangChain LLM client."""
    access_token = get_access_token()
    return ChatOpenAI(
        model=MODEL_NAME,
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        api_key=access_token,
        base_url=BASE_URL
    )


def read_unmatched_iforms(log_file: Path = None, stderr_output: str = None):
    """Extract unmatched IFORMs from log file or stderr output."""
    unmatched = set()
    if log_file and log_file.exists():
        with open(log_file, 'r') as f:
            for line in f:
                if "IFORM" in line and "not found in spec" in line:
                    iform = line.split()[4]  # e.g., REP_STOSD
                    unmatched.add(iform)
    elif stderr_output:
        for line in stderr_output.splitlines():
            if "IFORM" in line and "not found in spec" in line:
                iform = line.split()[4]
                unmatched.add(iform)
    return unmatched


def read_coverage_summary(csv_file: Path):
    """Read coverage summary from CSV report."""
    summary = {}
    if csv_file.exists():
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2 and row[0]:
                    summary[row[0]] = row[1]
    return summary


def read_sde_snippet(sde_file: Path, lines=50):
    """Read a snippet of SDE output for context."""
    if sde_file.exists():
        with open(sde_file, 'r') as f:
            return '\n'.join(f.readlines()[:lines])
    return "SDE output not available."


def generate_prompt(unmatched_iforms, coverage_summary, sde_snippet):
    """Create prompt for GPT-4o."""
    prompt = f"""
You are an expert in Intel x86_64 instruction set architecture and software optimization. Your task is to analyze instruction coverage data from a stress-ng workload run with Intel SDE and propose changes to increase coverage.

**Input Data**:
- Unmatched IFORMs (not in x86_64.yaml): {', '.join(unmatched_iforms) if unmatched_iforms else 'None'}
- Coverage Summary:
  - Total Instructions: {coverage_summary.get('Total Instructions', 'N/A')}
  - Unique Covered: {coverage_summary.get('Covered Instructions (Unique)', 'N/A')}
  - Coverage Percentage: {coverage_summary.get('Coverage Percentage', 'N/A')}
  - Top Category: {coverage_summary.get('Top Category', 'N/A')}
- SDE Output Snippet:
  ```
  {sde_snippet}
  ```

**Task**:
1. Propose specific entries for `config/instruction_specs/x86_64.yaml` to cover the unmatched IFORMs. Use the format:
   ```yaml
   IFORM_NAME:
     iclass: CLASS_NAME
     extension: EXTENSION
     category: CATEGORY
     isa_set: ISA_SET
     attributes: [ATTRIBUTE1, ATTRIBUTE2]
   ```
   Base your suggestions on Intel's XED documentation or common x86_64 patterns.
2. Suggest modifications to `run_stress_ng_sde.sh` to increase coverage, such as new stress-ng `--cpu-method` options or extended runtime. Provide a bash snippet.
3. Explain your reasoning for each proposal.

**Output Format**:
- YAML Suggestions:
  ```yaml
  # Suggested IFORMs
  ...
  ```
- Stress-ng Script Suggestions:
  ```bash
  # Suggested changes to run_stress_ng_sde.sh
  ...
  ```
- Reasoning:
  - IFORM Proposals: ...
  - Stress-ng Proposals: ...
"""
    return prompt


def run_stress_ng_for_logs():
    """Run make stress-ng and capture stderr for logs."""
    try:
        result = subprocess.run(
            ["make", "stress-ng"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stderr
    except subprocess.CalledProcessError as e:
        print(f"Error running make stress-ng: {e.stderr}")
        return ""


def extract_yaml_suggestions(suggestions: str):
    """Extract YAML content from AI suggestions."""
    yaml_pattern = r"```yaml\n# Suggested IFORMs\n([\s\S]*?)\n```"
    match = re.search(yaml_pattern, suggestions)
    return match.group(1) if match else ""


def apply_yaml_suggestions(yaml_content: str, spec_file: Path):
    """Append YAML suggestions to the spec file with user confirmation or default fallback."""
    if not yaml_content.strip():
        print("No YAML suggestions to apply.")
        return

    print("\nProposed YAML additions:")
    print(yaml_content)

    # Fallback to environment variable or 'n' if stdin is unavailable
    try:
        response = input(f"\nAppend these to {spec_file}? (y/n): ").strip().lower()
    except EOFError:
        response = os.getenv("AUTO_APPEND_YAML", "n").strip().lower()

    if response == 'y':
        with open(spec_file, 'a') as f:
            f.write('\n' + yaml_content)
        print(f"Appended suggestions to {spec_file}")
    else:
        print("Suggestions not applied.")


def write_suggestions(suggestions: str):
    """Write AI suggestions to file."""
    Path(OUTPUT_SUGGESTIONS).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_SUGGESTIONS, 'w') as f:
        f.write(suggestions)
    print(f"Suggestions saved to {OUTPUT_SUGGESTIONS}")


def main():
    """Main function to propose coverage changes."""
    # Try running stress-ng to generate logs if log file is missing
    log_path = Path(LOG_FILE)
    stderr_output = ""
    if not log_path.exists():
        print(f"Log file {LOG_FILE} not found. Running make stress-ng to generate logs...")
        stderr_output = run_stress_ng_for_logs()

    # Read input data
    unmatched_iforms = read_unmatched_iforms(log_path, stderr_output)
    coverage_summary = read_coverage_summary(Path(COVERAGE_CSV))
    sde_snippet = read_sde_snippet(Path(SDE_OUTPUT))

    if not unmatched_iforms and not stderr_output:
        print("No unmatched IFORMs found and no logs generated. Coverage may be optimal or logs are missing.")
        return

    # Create LLM client
    llm = create_llm()

    # Prepare messages
    prompt = generate_prompt(unmatched_iforms, coverage_summary, sde_snippet)
    messages = [
        SystemMessage(content="You are an expert assistant for x86_64 instruction coverage optimization."),
        HumanMessage(content=prompt)
    ]

    # Invoke model
    try:
        ai_response = llm.invoke(messages)
        write_suggestions(ai_response.content)
        yaml_content = extract_yaml_suggestions(ai_response.content)
        apply_yaml_suggestions(yaml_content, Path(SPEC_FILE))
    except Exception as e:
        print(f"Error invoking LLM: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()