# ATLAS Security NetOps Toolkit

ATLAS is a containerized Python command-line toolkit for network diagnostics and basic security log analysis.

It was built as a practical cybersecurity and IT portfolio project demonstrating Linux, networking, Python, security automation, testing, Docker and CI/CD.

## Features

- DNS resolution
- TCP connectivity testing
- HTTPS/TLS inspection
- TLS version and cipher inspection
- Certificate information
- SSH authentication log analysis
- Basic brute-force detection
- Human-readable and JSON output
- Automated unit tests
- Docker support
- Non-root container execution
- GitHub Actions CI

## Architecture

ATLAS uses a modular structure:

    User
      |
      v
    ATLAS CLI
      |
      +--> DNS Module
      |
      +--> TCP Module
      |
      +--> HTTPS/TLS Module
      |
      +--> Log Analysis Module
                |
                v
        Failed Login Detection
                |
                v
        Suspicious Source Report

## Installation

Create and activate a virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -e .

Check the CLI:

    atlas --help

## Usage

DNS lookup:

    atlas dns example.com

TCP connectivity:

    atlas tcp example.com 443

TLS inspection:

    atlas https example.com

Authentication log analysis:

    atlas logs sample-data/auth.log

JSON output:

    atlas --json dns example.com

## Example Detection

The included synthetic authentication log contains multiple failed SSH login attempts.

Example output:

    Failed SSH attempts: 9

    Source IPs:
      192.168.1.50: 7
      192.168.1.75: 1
      192.168.1.90: 1

    Potential brute-force sources:
      192.168.1.50: 7 failed attempts

The included log data is synthetic and contains no real user activity.

## Docker

Build ATLAS:

    sudo docker build -t atlas-netops .

Run it:

    sudo docker run --rm atlas-netops dns example.com

Run the log analyzer:

    sudo docker run --rm atlas-netops logs sample-data/auth.log

The container runs ATLAS as a dedicated non-root user.

For stricter runtime security:

    sudo docker run --rm --read-only --cap-drop=ALL --security-opt=no-new-privileges atlas-netops dns example.com

## Testing

Run the automated test suite:

    PYTHONPATH=src pytest -v

The current test suite covers:

- successful DNS resolution
- DNS failure handling
- successful TCP connectivity
- TCP failure handling
- authentication log analysis

## CI/CD

GitHub Actions automatically runs on pushes and pull requests to the main branch.

The pipeline:

    Push / Pull Request
            |
            +--> Python Tests
            |
            +--> Docker Build
            |
            +--> Verify Non-Root User
            |
            +--> Container Smoke Test

## Security Design

ATLAS applies several security practices:

- dedicated non-root container user
- support for read-only container execution
- Linux capabilities can be removed
- no-new-privileges support
- environment files excluded from Git
- automated tests
- read-only GitHub Actions repository permissions
- synthetic demonstration data

## Technologies

Python 3, Linux, TCP/IP, DNS, TLS, Git, GitHub, pytest, Docker and GitHub Actions.

## What I Learned

This project combines concepts from networking, Linux, programming and cybersecurity into one practical workflow.

The project gave me hands-on experience with DNS resolution, TCP sockets, TLS handshakes, authentication logs, Python exception handling, command-line application development, automated testing, containerization, least privilege and CI/CD.

## Limitations

ATLAS is an educational and portfolio project. It is not intended to replace enterprise SIEM, monitoring or vulnerability-management solutions.

Network functionality should only be used against systems and networks the user owns or has authorization to test.

## Future Improvements

- configurable brute-force thresholds
- IPv6 support
- structured logging
- additional TLS validation
- additional log formats
- SIEM export
- Sigma integration
- additional automated tests
- local atlas.lab environment
