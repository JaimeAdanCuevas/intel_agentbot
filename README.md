# Intel Agentbot
## Setup
- Install Docker.
- Place SDE and xed binaries in `./bin/`.
- Build container: `./scripts/build_container.sh`
## Usage
- Run tests: `docker run --rm intel-agentbot make test`
- Run stress-ng: `docker run --rm intel-agentbot make stress-ng`