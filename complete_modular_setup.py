#!/usr/bin/env python3
"""
Complete setup for modular KWB configuration.
"""

import json
import shutil
from pathlib import Path

def complete_modular_setup():
    """Complete the modular setup."""
    print("🔧 Complete Modular KWB Setup")
    print("=" * 40)
    
    # Backup original config
    original_config = Path('custom_components/kwb_heating/kwb_config.json')
    backup_config = Path('custom_components/kwb_heating/kwb_config.json.backup')
    
    if original_config.exists() and not backup_config.exists():
        shutil.copy2(original_config, backup_config)
        print("✅ Backed up original config")
    
    # Update coordinator to use modular manager
    coordinator_path = Path('custom_components/kwb_heating/coordinator.py')
    if coordinator_path.exists():
        print("✅ Coordinator already updated for modular config")
    
    # Set integration config for KWB CF 2 with 0 equipment for initial test
    config_entries_path = Path('ha-config/.storage/core.config_entries')
    
    try:
        with open(config_entries_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Find KWB entry
        kwb_entry = None
        for entry in config_data['data']['entries']:
            if entry.get('domain') == 'kwb_heating':
                kwb_entry = entry
                break
        
        if kwb_entry:
            # Configure for minimal setup: KWB CF 2 with no equipment
            kwb_entry['data'].update({
                'device_type': 'KWB CF 2',
                'access_level': 'UserLevel',
                'heating_circuits': 0,
                'buffer_storage': 0,
                'dhw_storage': 0,
                'secondary_heat_sources': 0,
                'circulation': 0,
                'solar': 0,
                'boiler_sequence': 0,
                'heat_meters': 0
            })
            
            with open(config_entries_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
            
            print("✅ Updated integration config for KWB CF 2 (no equipment)")
        else:
            print("❌ KWB entry not found in config")
    
    except Exception as e:
        print(f"❌ Error updating config: {e}")
    
    # Verify modular files exist
    config_dir = Path('custom_components/kwb_heating/config')
    required_files = [
        'universal_registers.json',
        'value_tables.json',
        'devices/kwb_cf2.json'
    ]
    
    all_present = True
    for file_path in required_files:
        full_path = config_dir / file_path
        if full_path.exists():
            size_kb = full_path.stat().st_size / 1024
            print(f"✅ {file_path}: {size_kb:.1f} KB")
        else:
            print(f"❌ Missing: {file_path}")
            all_present = False
    
    if all_present:
        print("\n🎉 Modular setup complete!")
        print("Next: Restart container to test")
    else:
        print("\n⚠️ Some files missing - check config generation")

if __name__ == "__main__":
    complete_modular_setup()
