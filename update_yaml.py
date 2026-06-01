#!/usr/bin/env python3
"""
Script to extract keys from mapping-gestalt.h and mapping-gestalt-legacy.h
and add them to mobile_gestalt.yaml (excluding simulator keys)
"""

import re
from pathlib import Path


def parse_header_file(file_path):
    """Parse a C header file and extract key mappings."""
    keys = {}

    with open(file_path, 'r') as f:
        content = f.read()

    # Find all key mappings: "hash", "name", // comment
    pattern = r'"([^"]+)",\s*"([^"]+)",\s*//\s*(.+)'

    for match in re.finditer(pattern, content):
        obfuscated_key = match.group(1)
        deobfuscated_name = match.group(2)
        comment = match.group(3).strip()

        if deobfuscated_name and deobfuscated_name != "NULL":
            keys[deobfuscated_name] = {
                'obfuscated': obfuscated_key,
                'comment': comment
            }

    return keys


def is_simulator_key(comment):
    """Check if a key is marked as simulator-only."""
    return 'Simulator' in comment


def read_existing_yaml(yaml_path):
    """Read existing YAML file and extract known keys."""
    existing_keys = set()
    existing_data = {}

    with open(yaml_path, 'r') as f:
        content = f.read()

    # Parse YAML manually - extract key names under known_keys:
    lines = content.split('\n')
    in_known_keys = False

    for i, line in enumerate(lines):
        if line.strip() == 'known_keys:':
            in_known_keys = True
            continue

        if in_known_keys and line.startswith('  ') and ':' in line and not line.startswith('    '):
            # This is a key entry
            key_name = line.strip().rstrip(':')
            existing_keys.add(key_name)

            # Extract obfuscated value (next 2-3 lines)
            obfuscated = None
            for j in range(i+1, min(i+4, len(lines))):
                if 'obfuscated:' in lines[j]:
                    obfuscated_line = lines[j].split('obfuscated:', 1)[1].strip()
                    # Remove quotes if present
                    obfuscated = obfuscated_line.strip('"\'')
                    break

            if obfuscated:
                existing_data[key_name] = obfuscated

    return existing_data, existing_keys


def generate_yaml_entry(key_name, obfuscated):
    """Generate a YAML entry for a key."""
    return f"""  {key_name}:
    description:
    obfuscated: {obfuscated}
    type:
"""


def main():
    # Paths
    mgkeys_dir = Path(__file__).parent
    mapping_gestalt_h = mgkeys_dir / 'mapping-gestalt.h'
    mapping_gestalt_legacy_h = mgkeys_dir / 'mapping-gestalt-legacy.h'
    yaml_path = mgkeys_dir.parent / 'apple-knowledge' / '_data' / 'mobile_gestalt.yaml'

    print(f"Reading {mapping_gestalt_h}")
    main_keys = parse_header_file(mapping_gestalt_h)
    print(f"  Found {len(main_keys)} keys")

    print(f"Reading {mapping_gestalt_legacy_h}")
    legacy_keys = parse_header_file(mapping_gestalt_legacy_h)
    print(f"  Found {len(legacy_keys)} keys")

    # Filter out simulator keys from legacy
    legacy_keys_filtered = {
        k: v for k, v in legacy_keys.items()
        if not is_simulator_key(v['comment'])
    }
    print(f"  After filtering simulator keys: {len(legacy_keys_filtered)} keys")

    # Combine all keys
    all_keys = {**main_keys, **legacy_keys_filtered}
    print(f"\nTotal unique keys: {len(all_keys)}")

    # Read existing YAML
    print(f"\nReading {yaml_path}")
    existing_data, existing_keys = read_existing_yaml(yaml_path)
    print(f"  Found {len(existing_keys)} existing keys")

    # Find new keys
    new_keys = {}
    for key_name, key_data in all_keys.items():
        if key_name not in existing_keys:
            new_keys[key_name] = key_data

    print(f"\nNew keys to add: {len(new_keys)}")

    if not new_keys:
        print("No new keys to add!")
        return

    # Sort all keys alphabetically (case-insensitive)
    all_yaml_keys = {}
    for key_name, obfuscated in existing_data.items():
        all_yaml_keys[key_name] = obfuscated
    for key_name, key_data in new_keys.items():
        all_yaml_keys[key_name] = key_data['obfuscated']

    sorted_keys = sorted(all_yaml_keys.keys(), key=str.lower)

    # Build new YAML content
    yaml_lines = [
        '---',
        'metadata:',
        '  description:',
        '  credits:',
        '  collections:',
        '  - known_keys',
        'known_keys:'
    ]

    for key_name in sorted_keys:
        obfuscated = all_yaml_keys[key_name]
        yaml_lines.append(f'  {key_name}:')
        yaml_lines.append('    description:')

        # Quote if contains special characters
        if obfuscated.startswith('/') or obfuscated.startswith('+'):
            yaml_lines.append(f'    obfuscated: "{obfuscated}"')
        else:
            yaml_lines.append(f'    obfuscated: {obfuscated}')

        yaml_lines.append('    type:')

    # Write back to file
    output_content = '\n'.join(yaml_lines) + '\n'

    with open(yaml_path, 'w') as f:
        f.write(output_content)

    print(f"\nSuccessfully updated {yaml_path}")
    print(f"Added {len(new_keys)} new keys:")
    for key in sorted(new_keys.keys(), key=str.lower)[:10]:
        print(f"  - {key}")
    if len(new_keys) > 10:
        print(f"  ... and {len(new_keys) - 10} more")


if __name__ == '__main__':
    main()
