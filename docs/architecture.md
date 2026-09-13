# ATLAS Architecture

## Overview

ATLAS is a modular Python command-line application for basic network diagnostics and security log analysis.

The CLI receives user input and delegates each operation to a specialized module.

## Application Flow

    User
      |
      v
    ATLAS CLI
      |
      +----------------+----------------+----------------+
      |                |                |                |
      v                v                v                v
    DNS              TCP           HTTPS/TLS        Log Analyzer
      |                |                |                |
      v                v                v                v
    Resolver       TCP Socket      TLS Handshake    Authentication Log
                                                        |
                                                        v
                                                Failed Login Detection
                                                        |
                                                        v
                                             Suspicious Source Report

## DNS Module

The DNS module resolves domain names into IP addresses using Python's socket interface.

It catches DNS-related errors so the application can return a controlled failure instead of crashing.

## TCP Module

The TCP module attempts to establish a connection to a user-specified host and port.

A connection timeout prevents unreachable services from causing ATLAS to wait indefinitely.

## HTTPS and TLS Module

The HTTPS/TLS module:

- creates a TCP connection
- establishes a TLS session
- retrieves the negotiated TLS version
- retrieves the cipher suite
- reads certificate information
- reports certificate expiration information

## Log Analysis Module

The log analyzer processes SSH authentication log entries.

It:

1. identifies failed login attempts
2. extracts source IP addresses
3. counts attempts by source
4. compares the count against a threshold
5. reports potential brute-force sources

## Testing Strategy

Unit tests are used to verify application behavior.

External network operations are mocked where appropriate so tests are deterministic and do not depend on public internet availability.

Current automated coverage includes:

- DNS success
- DNS failure
- TCP success
- TCP failure
- authentication log analysis

## Docker Architecture

ATLAS is packaged inside a lightweight Python container.

The container uses a dedicated non-root account:

    uid=10001(atlas)

Additional runtime protections can include:

    --read-only
    --cap-drop=ALL
    --security-opt=no-new-privileges

## CI Pipeline

GitHub Actions performs automated validation on pushes and pull requests to the main branch.

    Push / Pull Request
            |
            +--> Python Tests
            |
            +--> Docker Build
            |
            +--> Verify Non-Root User
            |
            +--> Container Smoke Test

The workflow uses read-only repository permissions where possible.

## Security Principles Demonstrated

ATLAS demonstrates several basic security engineering principles:

- least privilege
- controlled error handling
- dependency isolation
- automated testing
- immutable container execution
- synthetic test data
- secrets exclusion
- CI-based verification
