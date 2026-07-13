# Integration Subagent Guide

## Role
Coordinate a research case across requested capabilities without assuming a fixed stage order.

## Contract
Integration cases live under `examples/<research_case>/<child_case>/` and maintain `manifests/research_coordination_manifest.json`.

The manifest records requested capabilities, linked cases, capability status, blockers, and next actions. A capability that the user did not request must not become a blocker.

This layer does not edit business cases or create academic正文.
