import os
import requests
import csv
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

# Set proxies
os.environ['http_proxy'] = 'http://proxy-chain.intel.com:912'
os.environ['https_proxy'] = 'http://proxy-chain.intel.com:912'


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


def read_unmatched_iforms(log_file: Path):
    """Extract unmatched IFORMs from log file."""
    unmatched = set()
    with open(log_file, 'r') as f:
        for line in f:
            if "IFORM" in line and "not found in spec" in line:
                iform = line.split()[4]  # e.g., REP_STOSD
                unmatched.add(iform)
    return unmatched


def read_coverage_summary(csv_file: Path):
    """Read coverage summary from CSV report."""
    summary = {}
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Metric']:
                summary[row['Metric']] = row['Value']
    return summary


def read_sde_snippet(sde_file: Path, lines=50):
    """Read a snippet of SDE output for context."""
    with open(sde_file, 'r') as f:
        return '\n'.join(f.readlines()[:lines])


def generate_prompt(unmatched_iforms, coverage_summary, sde_snippet):
    """Create prompt for GPT-4o."""
    prompt = f"""
You are an expert in Intel x86_64 instruction set architecture and software optimization. Your task is to analyze instruction coverage data from a stress-ng workload run with Intel SDE and propose changes to increase coverage.

**Input Data**:
- Unmatched IFORMs (not in x86_64.yaml): {', '.join(unmatched_iforms)}
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


def write_suggestions(suggestions: str):
    """Write AI suggestions to file."""
    Path(OUTPUT_SUGGESTIONS).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_SUGGESTIONS, 'w') as f:
        f.write(suggestions)
    print(f"Suggestions saved to {OUTPUT_SUGGESTIONS}")


def main():
    """Main function to propose coverage changes."""
    # Read input data
    unmatched_iforms = read_unmatched_iforms(Path(LOG_FILE))
    coverage_summary = read_coverage_summary(Path(COVERAGE_CSV))
    sde_snippet = read_sde_snippet(Path(SDE_OUTPUT))

    if not unmatched_iforms:
        print("No unmatched IFORMs found. Coverage may be optimal.")
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
    except Exception as e:
        print(f"Error invoking LLM: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
