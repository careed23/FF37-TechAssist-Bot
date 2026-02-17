import yaml
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Step:
    """Represents a single step in a troubleshooting flow"""
    id: str
    question: str
    options: List[Dict]


@dataclass
class Solution:
    """Represents a resolution procedure"""
    id: str
    title: str
    steps: List[str]
    reference_doc: Optional[str] = None
    video: Optional[str] = None
    escalate_if: Optional[str] = None


class TroubleshootingEngine:
    """
    Core engine for managing troubleshooting flows and solutions
    """
    
    def __init__(self, flows_file: str = 'data/troubleshooting_flows.yaml'):
        """
        Initialize the engine with troubleshooting flows
        
        Args:
            flows_file: Path to YAML file containing flows and solutions
        """
        self.flows_file = Path(flows_file)
        
        if not self.flows_file.exists():
            raise FileNotFoundError(f"Flows file not found: {flows_file}")
        
        with open(self.flows_file, 'r') as f:
            data = yaml.safe_load(f)
        
        self.flows = data.get('flows', [])
        self.solutions = {
            s['id']: Solution(**s) 
            for s in data.get('solutions', [])
        }
        
    def list_flows(self) -> List[Dict]:
        """
        Get list of all available troubleshooting flows
        
        Returns:
            List of flow dictionaries with id, name, description
        """
        return [
            {
                'id': flow['id'],
                'name': flow['name'],
                'description': flow.get('description', '')
            }
            for flow in self.flows
        ]
    
    def get_flow(self, flow_id: str) -> Optional[Dict]:
        """
        Get a specific troubleshooting flow by ID
        
        Args:
            flow_id: Unique identifier for the flow
            
        Returns:
            Flow dictionary or None if not found
        """
        for flow in self.flows:
            if flow['id'] == flow_id:
                return flow
        return None
    
    def get_first_step(self, flow_id: str) -> Optional[Dict]:
        """
        Get the first step of a troubleshooting flow
        
        Args:
            flow_id: Unique identifier for the flow
            
        Returns:
            Step dictionary or None if flow not found
        """
        flow = self.get_flow(flow_id)
        if not flow or not flow.get('steps'):
            return None
        
        first_step = flow['steps'][0]
        return {
            'type': 'step',
            'data': first_step
        }
    
    def get_step_by_id(self, flow_id: str, step_id: str) -> Optional[Dict]:
        """
        Get a specific step from a flow by step ID
        
        Args:
            flow_id: Unique identifier for the flow
            step_id: Unique identifier for the step within the flow
            
        Returns:
            Step dictionary wrapped in result format or None
        """
        flow = self.get_flow(flow_id)
        if not flow:
            return None
        
        for step in flow.get('steps', []):
            if step.get('id') == step_id:
                return {
                    'type': 'step',
                    'data': step
                }
        
        return None
    
    def get_next_action(self, flow_id: str, current_step_id: str, choice_value: str) -> Optional[Dict]:
        """
        Determine the next action based on user's choice
        
        Args:
            flow_id: Current flow ID
            current_step_id: Current step ID
            choice_value: Value of the option the user selected
            
        Returns:
            Dictionary with either next step or solution, or None if invalid
        """
        # Get current step
        current_step_result = self.get_step_by_id(flow_id, current_step_id)
        
        if not current_step_result or current_step_result['type'] != 'step':
            return None
        
        current_step = current_step_result['data']
        
        # Find the selected option
        for option in current_step.get('options', []):
            if option['value'] == choice_value:
                # Check if this option leads to next step
                if 'next' in option:
                    return self.get_step_by_id(flow_id, option['next'])
                
                # Check if this option leads to a solution
                elif 'solution' in option:
                    solution = self.get_solution(option['solution'])
                    if solution:
                        return {
                            'type': 'solution',
                            'data': solution
                        }
                
        return None
    
    def get_solution(self, solution_id: str) -> Optional[Solution]:
        """
        Get a solution by ID
        
        Args:
            solution_id: Unique identifier for the solution
            
        Returns:
            Solution object or None if not found
        """
        return self.solutions.get(solution_id)
    
    def validate_flows(self) -> List[str]:
        """
        Validate that all flows are properly structured
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        for flow in self.flows:
            errors.extend(self._validate_flow(flow))
        
        # Validate solutions
        for solution_id, solution in self.solutions.items():
            if not solution.title:
                errors.append(f"Solution {solution_id}: Missing 'title' field")
            if not solution.steps:
                errors.append(f"Solution {solution_id}: No steps defined")
        
        return errors

    def _validate_flow(self, flow: Dict) -> List[str]:
        """Validate a single flow's structure."""
        errors = []
        flow_id = flow.get('id', 'UNKNOWN')

        if not flow.get('name'):
            errors.append(f"Flow {flow_id}: Missing 'name' field")
        if not flow.get('description'):
            errors.append(f"Flow {flow_id}: Missing 'description' field")
        if not flow.get('steps'):
            errors.append(f"Flow {flow_id}: No steps defined")
            return errors

        for step in flow['steps']:
            errors.extend(self._validate_step(flow_id, step))

        return errors

    def _validate_step(self, flow_id: str, step: Dict) -> List[str]:
        """Validate a single step within a flow."""
        errors = []
        step_id = step.get('id', 'UNKNOWN')

        if not step.get('question'):
            errors.append(f"Flow {flow_id}, Step {step_id}: Missing 'question' field")
        if not step.get('options'):
            errors.append(f"Flow {flow_id}, Step {step_id}: No options defined")
            return errors

        for idx, option in enumerate(step['options']):
            errors.extend(self._validate_option(flow_id, step_id, idx, option))

        return errors

    def _validate_option(self, flow_id: str, step_id: str, idx: int, option: Dict) -> List[str]:
        """Validate a single option within a step."""
        errors = []

        if not option.get('value'):
            errors.append(f"Flow {flow_id}, Step {step_id}, Option {idx}: Missing 'value' field")
        if not option.get('description'):
            errors.append(f"Flow {flow_id}, Step {step_id}, Option {idx}: Missing 'description' field")

        if 'next' not in option and 'solution' not in option:
            errors.append(
                f"Flow {flow_id}, Step {step_id}, Option '{option.get('value')}': "
                f"Must have either 'next' or 'solution' field"
            )

        if 'solution' in option and option['solution'] not in self.solutions:
            errors.append(
                f"Flow {flow_id}, Step {step_id}, Option '{option.get('value')}': "
                f"References non-existent solution '{option['solution']}'"
            )

        return errors


# Utility functions

def load_engine(flows_file: str = 'data/troubleshooting_flows.yaml') -> TroubleshootingEngine:
    """
    Helper function to load and validate a troubleshooting engine
    
    Args:
        flows_file: Path to YAML flows file
        
    Returns:
        TroubleshootingEngine instance
        
    Raises:
        ValueError: If flows file has validation errors
    """
    engine = TroubleshootingEngine(flows_file)
    
    errors = engine.validate_flows()
    if errors:
        error_msg = "Flow validation errors found:\n" + "\n".join(errors)
        raise ValueError(error_msg)
    
    return engine


# For testing
if __name__ == "__main__":
    try:
        engine = load_engine()
        print("✓ Flow engine loaded successfully")
        print(f"✓ Found {len(engine.flows)} troubleshooting flows")
        print(f"✓ Found {len(engine.solutions)} solutions")
        
        # List available flows
        print("\nAvailable flows:")
        for flow in engine.list_flows():
            print(f"  - {flow['name']}")
        
        # Validate
        errors = engine.validate_flows()
        if errors:
            print("\n⚠ Validation errors:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("\n✓ All flows validated successfully")
            
    except Exception as e:
        print(f"✗ Error: {e}")
