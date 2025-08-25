#!/usr/bin/env python
"""Import test for quantforge module"""

import sys

print(f"Python: {sys.version}")
print(f"Path: {sys.path[:2]}")

try:
    import quantforge

    print(f"\nModule imported: {quantforge}")
    print(f"Module file: {quantforge.__file__}")

    funcs = [x for x in dir(quantforge) if not x.startswith("_")]
    print(f"\nAvailable functions ({len(funcs)}):")
    for func in sorted(funcs):
        print(f"  - {func}")

    # Try to access the function directly
    if hasattr(quantforge, "calculate_delta_call"):
        print("\n✓ calculate_delta_call found!")
    else:
        print("\n✗ calculate_delta_call NOT found")

    # Check submodules
    if hasattr(quantforge, "quantforge"):
        print("\nFound submodule 'quantforge'")
        subfuncs = [x for x in dir(quantforge.quantforge) if "delta" in x.lower()]
        print(f"Submodule greeks functions: {subfuncs}")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
