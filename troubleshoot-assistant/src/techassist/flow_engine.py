import yaml
import os
from pathlib import Path

class TroubleshootingEngine:
    def __init__(self, flows_file: str = 'data/troubleshooting_flows.yaml'):
        
        self.flows = []
        self.solutions = {}
        
        flows_path = Path(flows_file)
        
        # If a directory is passed, load ALL yaml files in it
        if flows_path.is_dir():
            yaml_files = list(flows_path.glob('*.yaml')) + list(flows_path.glob('*.yml'))
            if not yaml_files:
                raise FileNotFoundError(f"No YAML files found in directory: {flows_path}")
            
            print(f"Loading {len(yaml_files)} workflow files...")
            for yaml_file in sorted(yaml_files):
                self._load_file(yaml_file)
                print(f"  Loaded: {yaml_file.name}")
        
        # If a single file is passed, load just that file
        elif flows_path.is_file():
            self._load_file(flows_path)
        
        else:
            raise FileNotFoundError(f"Flows file or directory not found: {flows_file}")
    
    def _load_file(self, file_path: Path):
        """Load a single YAML file and merge into existing flows/solutions"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data:
            return
        
        # Merge flows
        new_flows = data.get('flows', [])
        self.flows.extend(new_flows)
        
        # Merge solutions - check for duplicate IDs
        new_solutions = data.get('solutions', [])
        for s in new_solutions:
            sol_id = s['id']
            if sol_id in self.solutions:
                print(f"  WARNING: Duplicate solution ID '{sol_id}' in {file_path.name} - overwriting")
            self.solutions[sol_id] = Solution(**s)
```

Then organize your data folder like this:
```
data/
  troubleshooting_flows.yaml       # existing workflows
  ont_port_change_flows.yaml       # new workflows
  splitter_leg_flows.yaml          # future workflows
  ont_size_flows.yaml              # future workflows