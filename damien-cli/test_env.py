
import os
import sys
import site

# Print Python version and environment details
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Print site-packages directories
print("\nSite packages directories:")
for path in site.getsitepackages():
    print(path)

# List installed packages
print("\nInstalled packages:")
packages = ["torch", "sentence_transformers", "numpy", "transformers"]
for package in packages:
    try:
        module = __import__(package)
        print(f"{package}: Found at {module.__file__}, version {module.__version__}")
    except ImportError:
        print(f"{package}: Not found")
    except Exception as e:
        print(f"{package}: Error - {str(e)}")

print("\nTest completed!")
