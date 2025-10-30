#!/usr/bin/env python3
from agent_framework import HandoffBuilder
import inspect

print("HandoffBuilder methods:")
methods = [m for m in dir(HandoffBuilder) if not m.startswith('_')]
for m in sorted(methods):
    print(f"  {m}")

print("\n\nHandoffBuilder constructor signature:")
print(inspect.signature(HandoffBuilder.__init__))

print("\n\nAll HandoffBuilder attributes/methods:")
for name in sorted(dir(HandoffBuilder)):
    if not name.startswith('_'):
        attr = getattr(HandoffBuilder, name)
        if callable(attr):
            try:
                sig = inspect.signature(attr)
                print(f"  {name}{sig}")
            except:
                print(f"  {name}()")
        else:
            print(f"  {name} = {type(attr).__name__}")
