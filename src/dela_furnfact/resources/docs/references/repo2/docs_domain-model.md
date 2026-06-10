# Domain Model

## Layers

```txt
Intent Layer
Layout Layer
Solved Layer
Manufacturing Layer
Visualization Layer
```

## Core Concepts

- `FurnitureIntent`: what the user wants.
- `LayoutCandidate`: an abstract spatial proposal.
- `Zone`: useful storage space.
- `SolvedFurniture`: resolved carpentry model.
- `ManufacturingModel`: real parts and production data.

## Important Separation

A `Zone` is not a `Shelf`.

- `Zone`: functional storage space.
- `Shelf`: physical horizontal part derived later.
