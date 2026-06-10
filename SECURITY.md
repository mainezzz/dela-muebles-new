# Security Policy

## Supported versions
Only the latest tagged release is supported for fixes.

## Reporting a vulnerability
Do not open a public issue for security-sensitive findings.
Report privately to the project owner with:
- summary
- impact
- reproduction steps
- suggested mitigation

## Scope
This application does not ship cloud services. The main risks are:
- unsafe local file handling
- subprocess execution paths
- packaging or dependency issues
- malicious input files
