#!/bin/bash
# Robust stress-ng installer supporting Ubuntu, Debian, CentOS, RHEL, Fedora
# Installs stress-ng if not already installed
# Exits on error, logs steps clearly

set -euo pipefail
IFS=$'\n\t'

log() {
    echo -e "[INFO] $*"
}

error() {
    echo -e "[ERROR] $*" >&2
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

install_stress_ng_apt() {
    log "Updating apt package lists..."
    sudo apt-get update -y
    log "Installing stress-ng via apt..."
    sudo apt-get install -y stress-ng
}

install_stress_ng_yum() {
    log "Installing EPEL repository if needed..."
    if ! rpm -qa | grep -qw epel-release; then
        sudo yum install -y epel-release
    fi
    log "Installing stress-ng via yum..."
    sudo yum install -y stress-ng
}

install_stress_ng_dnf() {
    log "Installing stress-ng via dnf..."
    sudo dnf install -y stress-ng
}

main() {
    if command_exists stress-ng; then
        log "stress-ng is already installed at $(command -v stress-ng). Skipping installation."
    else
        log "stress-ng not found. Detecting OS and installing..."

        if [[ -f /etc/os-release ]]; then
            # shellcheck disable=SC1091
            . /etc/os-release
        else
            error "Cannot detect OS type (/etc/os-release not found). Aborting."
            exit 1
        fi

        case "$ID" in
            ubuntu|debian)
                install_stress_ng_apt
                ;;
            centos|rhel)
                install_stress_ng_yum
                ;;
            fedora)
                install_stress_ng_dnf
                ;;
            *)
                error "Unsupported OS: $ID. Please install stress-ng manually."
                exit 1
                ;;
        esac
    fi

    log "Verifying stress-ng installation..."
    if ! command_exists stress-ng; then
        error "stress-ng installation failed or binary not found in PATH."
        exit 1
    fi

    log "Creating local bin directory 'bin' if not exists..."
    mkdir -p bin

    local_stress_ng_path="bin/stress-ng"
    if [[ ! -x "$local_stress_ng_path" ]]; then
        cp "$(command -v stress-ng)" "$local_stress_ng_path"
        log "Copied stress-ng to $local_stress_ng_path"
    else
        log "stress-ng already copied to $local_stress_ng_path"
    fi

    log "Running stress-ng test: CPU 1 core for 5 seconds"
    "$local_stress_ng_path" --cpu 1 --timeout 5s --metrics-brief

    log "stress-ng setup complete."
}

main "$@"
