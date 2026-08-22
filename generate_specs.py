#!/usr/bin/env python3
"""
Generate three PyInstaller spec files with different architectures:
- rbMigrate-arm.spec (Apple Silicon only)
- rbMigrate-intel.spec (Intel only)
- rbMigrate-universal.spec (Both architectures)
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
    'universal': 'universal2',
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
