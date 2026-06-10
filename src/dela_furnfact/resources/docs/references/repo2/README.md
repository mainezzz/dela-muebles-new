# DELA Muebles Generator

Parametric furniture solver focused on storage-first design, carpentry-aware constraints, intelligent layouts, and manufacturing-ready outputs.

## Philosophy

The user designs:

- storage
- proportions
- aesthetics
- capacity

The system resolves:

- structure
- layouts
- rigidity
- manufacturing
- geometry

## Architecture

```txt
Intent
↓
LayoutCandidate
↓
SolvedFurniture
↓
ManufacturingModel
↓
Visualization
```

## Current Status

Foundation phase.

## Run demo

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
dela demo
```
