Intel Agentbot
A tool for analyzing Intel x86_64 instruction coverage using stress-ng, Intel SDE, and AI-driven optimization.
Prerequisites

Docker
SDE and xed binaries (place in ./bin/)
stress-ng binary (place in ./bin/)
Intel API credentials (CLIENT_ID, CLIENT_SECRET) for GPT-4o access

Project Structure
.
├── bin/
│   ├── sde
│   ├── xed
│   └── stress-ng
├── config/
│   └── instruction_specs/
│       └── x86_64.yaml
├── src/
│   └── core/
│       └── coverage/
│           ├── analyzer.py
│           └── propose_coverage_changes.py
├── tests/
│   ├── integration/
│   │   └── data/
│   │       ├── stress-ng-cpu-mix-out.txt
│   │       ├── coverage_report.csv
│   │       └── coverage_suggestions.txt
│   └── unit/
│       └── test_analyzer.py
├── scripts/
│   ├── build_container.sh
│   ├── monitor_iforms.sh
│   ├── verify_step1.sh
│   └── deployment/
│       └── run_stress_ng_sde.sh
├── Dockerfile
├── requirements.txt
├── Makefile
└── README.md

Setup

Clone the repository:
git clone <repository-url>
cd intel-agentbot


Place SDE, xed, and stress-ng binaries in ./bin/.

Set environment variables for Intel API:
export CLIENT_ID=<your-client-id>
export CLIENT_SECRET=<your-client-secret>


Build the Docker container:
chmod +x scripts/build_container.sh
./scripts/build_container.sh



Usage

Run Tests:
docker run --rm -e CLIENT_ID=<your-client-id> -e CLIENT_SECRET=<your-client-secret> intel-agentbot make test


Run stress-ng Workflow:
docker run --rm -e CLIENT_ID=<your-client-id> -e CLIENT_SECRET=<your-client-secret> intel-agentbot make stress-ng


Propose Coverage Improvements:
chmod +x scripts/monitor_iforms.sh
./scripts/monitor_iforms.sh


Outputs AI suggestions in tests/integration/data/coverage_suggestions.txt.


Verify Setup:
chmod +x scripts/verify_step1.sh
./scripts/verify_step1.sh



AI-Driven Optimization
The project uses GPT-4o via Intel’s internal API to propose coverage improvements:

propose_coverage_changes.py analyzes logs and coverage data, suggesting x86_64.yaml entries and stress-ng configurations.
Run monitor_iforms.sh to trigger AI proposals.
Apply suggestions manually to x86_64.yaml and run_stress_ng_sde.sh.

Maintenance

Update Instruction Specs:

Review tests/integration/data/coverage_suggestions.txt for AI-proposed IFORMs.
Update config/instruction_specs/x86_64.yaml accordingly.


Expand Coverage:

Apply AI-suggested stressors in scripts/deployment/run_stress_ng_sde.sh:${SDE_PATH} -mix -- ${STRESS_NG_PATH} --cpu 1 --cpu-method matrix,fft,prime,all --timeout 60s




Update Dependencies:

Edit requirements.txt and rebuild the container:./scripts/build_container.sh





Troubleshooting

ModuleNotFoundError:

Ensure PYTHONPATH=/app/src in Dockerfile or build_container.sh.
Verify src directory is mounted in the container.


Missing IFORMs:

Check monitor_iforms.sh output for coverage_suggestions.txt.



Update chmod with suggested changes.


Low Coverage:

Increase stress-ng timeout or add stressors in run_stress_ng_sde.sh.
Re-run monitor_iforms.sh to ensure coverage is optimized.


AI API Errors:

Verify CLIENT_ID and CLIENT_SECRET environment variables.
Check proxy settings (http://http://proxy-chain.intel.com:912).





**Action**:
- Save `README.md` in the project root directory.
- Replace `<repository-url>` with your actual repository URL.
- Replace `<your-client-id>` and `<your-client-secret>` with placeholders or instructions.

---

### Verification Steps

To confirm the AI integration and coverage improvements:

1. **Apply Updates**:
   - Save all provided files: `propose_coverage_changes.py`, `monitor_iforms.sh`, `run_stress_ng.sh`, `Dockerfile`, `requirements.txt`, `README.md`.
   - Update `x86_64.yaml` with missing IFORMs (if not already done).
   - Update `requirements.txt` with new dependencies.

1. **Rebuild Container**:
   ```bash
   export CLIENT_ID=<your-client-id>
   export CLIENT_SECRET=<your-client-secret>
   ./scripts/build_container.sh


Run AI Proposals:
./scripts/monitor_iforms.sh


Check tests/integration/data/coverage_suggestions.txt for YAML/ and bash suggestions.
Apply suggestions to x86_64.yaml files and run_stress_ng.sh.


Verify Tests:
docker run --rm -e CLIENT_ID=<your-id-id> -e CLIENT_SECRET=<your-client-id-secret> intel-agentbot make test
docker run


Ensure tests pass.
Run stress-ng:



docker run --rm -e CLIENT_ID= -e CLIENT_SECRET= client-secret intel-agentbot make stress-ng
- Check for increased `Unique Covered` (e.g., >266).


Provide Verification Outputs:

Share:


./scripts/verify_step1.sh
./bin/sde -v
./bin/x
./bin/xed -v
./bin/stress-ng
--version
cat /etc/os-release
grep -E "REP_STOSB|MOVZX|ADD" config/instruction_specs/x86_64.yaml

- Share `make stress-ng` output after applying AI suggestions.
- Provide `build_container.sh`, `Dockerfile`, and `Makefile` content.




Responding to Verification Outputs Request
You requested outputs for:

./scripts/verify_step1.sh
./bin/sde -v, ./bin/xed -v, ./bin/stress-ng --version, cat /etc/os-release
grep -E "REP_STOSB|MOVZX|ADD" config/instruction_specs/x86_64.yaml

Since you confirmed everything is working, I assume these outputs are available but not yet shared. Please provide them to verify the setup and coverage improvements. For example:

make stress-ng output after adding IFORMs should show Unique Covered > 266 and Coverage Percentage > 8.85%.
grep output should confirm REP_STOSB, MOVZX, and ADD entries in x86_64.yaml.


Additional Enhancements

Automated IFORM Application:
Extend propose_coverage_changes.py to automatically append AI-suggested IFORMs to x86_64.yaml with user confirmation:def apply_yaml_suggestions(yaml_content: str, spec_file: Path):
    with open(spec_file, 'a') as f:
        f.write('\n' + yaml_content)
    print(f"Appended suggestions to {spec_file}")




Coverage Visualization:
Add a plotting feature to analyzer.py to generate coverage charts:{
  "type": "chartjs",
  "data": {
    "type": "bar",
    "data": {
      "labels": ["Covered", "Uncovered"],
      "datasets": [{
        "label": "Instruction Coverage",
        "data": [self.coverage_stats['covered'], self.coverage_stats['total_instructions'] - self.coverage_stats['covered']],
        "backgroundColor": ["#36A2EB", "#FF6384"]
      }]
    },
    "options": {
      "scales": {
        "y": {
          "beginAtZero": true,
          "title": {
            "display": true,
            "text": "Number of Instructions"
          }
        },
        "x": {
          "title": {
            "display": true,
            "text": "Coverage Status"
          }
        }
      },
      "plugins": {
        "title": {
          "display": true,
          "text": "Instruction Coverage Summary"
        }
      }
    }
  }
}




CI/CD Pipeline:
Create a GitHub Actions workflow:name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build and Test
      env:
        CLIENT_ID: ${{ secrets.CLIENT_ID }}
        CLIENT_SECRET: ${{ secrets.CLIENT_SECRET }}
      run: |
        ./scripts/build_container.sh






Requested Information
To verify the AI integration and plan further steps, please provide:

Output of:./scripts/verify_step1.sh
./bin/sde -v
./bin/xed -v
./bin/stress-ng --version
cat /etc/os-release
grep -E "REP_STOSB|MOVZX|ADD" config/instruction_specs/x86_64.yaml


Output of make stress-ng after applying AI-suggested IFORMs and stressors.
Content of build_container.sh, Dockerfile, and Makefile.
Any errors from running monitor_iforms.sh or propose_coverage_changes.py.
Specific goals for the AI integration (e.g., target coverage %, automation level).

With these details, I’ll confirm the integration, refine the solution, or add new features. Thank you for your progress, and let’s make this AI-driven optimization shine!
