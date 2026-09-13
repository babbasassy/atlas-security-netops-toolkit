# Security Policy

## Purpose

ATLAS is an educational cybersecurity and network operations project.

It should only be used against systems, services, files, and networks that you own or are explicitly authorized to test.

## Secrets

Passwords, API keys, tokens, private keys, credentials, and other sensitive information must never be committed to this repository.

The `.gitignore` file excludes `.env` files from version control.

## Container Security

The ATLAS Docker image runs using a dedicated non-root user.

For stricter runtime isolation, ATLAS can be executed with:

    sudo docker run --rm       --read-only       --cap-drop=ALL       --security-opt=no-new-privileges       atlas-netops dns example.com

## Test Data

Authentication logs included in this repository are synthetic and are intended only for testing and demonstration.

## Responsible Use

ATLAS is not intended for unauthorized scanning, exploitation, or access.

Network functionality should only be used where explicit authorization exists.

## Reporting Security Issues

If a security issue is discovered in this project, sensitive exploit details should not be publicly disclosed before the issue has been reviewed and corrected.
