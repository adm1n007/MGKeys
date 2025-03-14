from deobfuscated import keys
from deobfuscated_legacy import keys_legacy
from obfuscate import calculate_obfuscated_key, md5_string_for_obfuscated_key
from keys_desc import NON_KEY_DESC, known_keys_desc, unknown_keys_desc

'''
This script generates a mapping file (mapping.h) for all keys in hashes.txt and hashes_legacy.txt. The mapped values are the deobfuscated keys.
This script also generates a potfile (potfile) for hashcat.
'''

HASHES = 'hashes.txt'
HASHES_LEGACY = 'hashes_legacy.txt'
MAPPING = 'mapping.h'
MAPPING_GESTALT = 'mapping-gestalt.h'
MAPPING_LEGACY = 'mapping-legacy.h'
TABLE = 'keyMappingTable'
TABLE_LEGACY = 'keyMappingTableLegacy'
POTFILE = 'potfile'
GEN_NON_GESTALT_KEY = True
USE_MAPPING_AS_SOURCE = False

POTFILE_CONTENT = ''

def map(hashes_file, mapping_file, table_name, only_gestalt, the_keys):
    keys = the_keys.copy()
    mapping = {}
    deobfuscated_keys = 0
    deobfuscated_gestalt_keys = 0
    non_gestalt_keys = 0
    unexplored_keys = 0

    def add_key(hash):
        global POTFILE_CONTENT
        nonlocal deobfuscated_gestalt_keys, non_gestalt_keys, deobfuscated_keys, only_gestalt
        if calculate_obfuscated_key(keys[hash]) != hash:
            print(f'Error: {hash} is not deobfuscated to {keys[hash]}')
            exit(1)
        md5 = md5_string_for_obfuscated_key(hash)
        if not only_gestalt:
            POTFILE_CONTENT += f'{md5}:MGCopyAnswer{keys[hash]}\n'
        keys[hash] = keys[hash].replace('"', '\\"')
        if hash in known_keys_desc:
            desc = known_keys_desc[hash]
            if NON_KEY_DESC in desc:
                if only_gestalt or not GEN_NON_GESTALT_KEY:
                    return False
                non_gestalt_keys += 1
            else:
                deobfuscated_gestalt_keys += 1
            mapping[hash] = f'"{keys[hash]}", // {desc}'
        else:
            deobfuscated_gestalt_keys += 1
            mapping[hash] = f'"{keys[hash]}",'
        deobfuscated_keys += 1
        return True

    with open(hashes_file, 'r') as hashes:
        with open(mapping_file, 'w') as out:
            for raw_hash in hashes:
                hash = raw_hash.strip()
                if hash in keys:
                    if not add_key(hash):
                        continue
                elif hash in unknown_keys_desc:
                    desc = unknown_keys_desc[hash]
                    if NON_KEY_DESC in desc:
                        if only_gestalt or not GEN_NON_GESTALT_KEY:
                            continue
                        non_gestalt_keys += 1
                    mapping[hash] = f'NULL, // {desc}'
                else:
                    unexplored_keys += 1
                    mapping[hash] = 'NULL,'
            for hash in keys:
                if hash not in mapping:
                    if USE_MAPPING_AS_SOURCE:
                        if not add_key(hash):
                            continue
                    else:
                        print(f'Warning: {hash} not found in {hashes_file}')
            mapping = dict(sorted(mapping.items(), key=lambda x: x[0].lower()))
            total = len(mapping)
            out.write('#include "struct.h"\n\n')
            out.write(f'// Total: {total} keys\n')
            out.write(f'// Deobfuscated: {deobfuscated_keys} keys ({round((deobfuscated_keys / total) * 100, 2)}%)\n')
            if not only_gestalt:
                out.write(f'// Total gestalt keys: {total - non_gestalt_keys} keys\n')
                out.write(f'// Deobfuscated gestalt: {deobfuscated_gestalt_keys} keys ({round((deobfuscated_gestalt_keys / (total - non_gestalt_keys)) * 100, 2)}%)\n')
            out.write(f'// Unexplored: {unexplored_keys} keys\n')
            out.write('\n')
            out.write(f'static const struct tKeyMapping {table_name}[] = {{\n')
            for hash in mapping:
                out.write(f'    "{hash}", {mapping[hash]}\n')
            out.write('    NULL, NULL\n};\n')

map(HASHES, MAPPING, TABLE, False, keys)
map(HASHES, MAPPING_GESTALT, TABLE, True, keys)
map(HASHES_LEGACY, MAPPING_LEGACY, TABLE_LEGACY, False, keys_legacy)

with open(POTFILE, 'w') as out:
    out.write(POTFILE_CONTENT)
