#!/usr/bin/env python3
"""
Generate PyInstaller spec files with different architectures:
- rbMigrate-arm.spec (Apple Silicon only)
- rbMigrate-intel.spec (Intel only)

Note: no universal2 build — numpy and psutil don't publish universal2
wheels, so a fat binary can't be produced from pip-installed deps.
"""

import re
import sys

# Read the base spec file
with open('rbMigrate.spec', 'r') as f:
    spec_content = f.read()

# Define the architectures
architectures = {
    'arm': 'arm64',
    'intel': 'x86_64',
}

# Generate spec files for each architecture
for name, arch in architectures.items():
    # Replace the target_arch line
    new_content = re.sub(
        r'target_arch=\w+',
        f'target_arch="{arch}"',
        spec_content
    )

    # Write the new spec file
    output_file = f'rbMigrate-{name}.spec'
    with open(output_file, 'w') as f:
        f.write(new_content)

    print(f"Generated {output_file} with {arch} architecture")

print("\nDone! Now you can build:")
print("  ./build_macos.sh")
