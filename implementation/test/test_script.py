import sys
import time

print("=== Python Test Script ===")
print("Arguments received:")
for i, arg in enumerate(sys.argv):
    print(f"Arg {i}: [{arg}]")

print("\nSimulating some work...")
for i in range(3):
    print(f"Working {i+1}/3...")
    time.sleep(1)

print("Done!")
