# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in ptir5, please report it responsibly.

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, please email security concerns to the maintainers via the contact information on the [Photothermal Spectroscopy Corp. website](https://www.photothermal.com/).

### What to include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### What to expect

- **Acknowledgment**: Within 5 business days of your report.
- **Assessment**: We will evaluate the severity and impact within 10 business days.
- **Resolution**: Critical vulnerabilities will be patched as soon as possible. We will coordinate disclosure timing with you.

## Scope

ptir5 is a read-only library that parses HDF5 files. Security concerns most likely relate to:

- Malformed HDF5 input causing crashes or unexpected behavior
- Denial of service via crafted files
- Dependencies (h5py, numpy) with known vulnerabilities
