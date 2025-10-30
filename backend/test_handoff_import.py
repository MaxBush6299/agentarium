#!/usr/bin/env python3
import agent_framework

print("Checking for Handoff/Orchestration classes:")
members = [m for m in dir(agent_framework) if 'Handoff' in m or 'Orchestr' in m]
print("Found:", members if members else "None")

print("\nAll exported classes containing 'work' or 'Handoff':")
exports = [m for m in dir(agent_framework) if 'work' in m.lower() or 'handoff' in m.lower()]
for e in sorted(exports):
    print(f"  {e}")

print("\nSearching for HandoffBuilder specifically...")
try:
    from agent_framework import HandoffBuilder
    print("✓ HandoffBuilder found!")
except ImportError as e:
    print(f"✗ HandoffBuilder not found: {e}")

print("\nAll available orchestration/workflow classes:")
exports = [m for m in dir(agent_framework) if not m.startswith('_')]
for e in sorted(exports):
    print(f"  {e}")
