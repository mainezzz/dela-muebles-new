# Architecture

## Core Philosophy

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

## Main Pipeline

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

## Key Rule

Blender, GLB, CSV, CNC, or any renderer/exporter must consume solved models. They must not contain core furniture logic.
