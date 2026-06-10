# Solver

## Goal

Transform user intent into a resolved, carpentry-aware furniture model.

## Pipeline

```txt
FurnitureIntent
↓
LayoutSolver
↓
RuleEngine
↓
Scoring
↓
SolvedFurniture
```

## Principle

The solver generates several candidates, evaluates them, and chooses the best one.
