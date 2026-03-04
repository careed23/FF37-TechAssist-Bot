import yaml
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

class FlowDefinitionError(Exception):
    """Custom exception for errors in flow definitions."""


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

    def __init__(self, flows_file: str = 'data'):
        """
        Initialize the engine with troubleshooting flows

        Args:
            flows_file: Path to YAML file or directory containing flows and solutions
        """
        self.logger = logging.getLogger(__name__)
        self.flows = []
        self.solutions = {}

        flows_path = Path(flows_file)

        # If a directory is passed, load ALL yaml files in it
        if flows_path.is_dir():
            yaml_files = list(flows_path.glob('*.yaml')) + list(flows_path.glob('*.yml'))
            if not yaml_files:
                self.logger.error(f"No YAML files found in directory: {flows_path}")
                raise FileNotFoundError(f"No YAML files found in directory: {flows_path}")

            self.logger.info(f"Loading {len(yaml_files)} workflow files...")
            for yaml_file in sorted(yaml_files):
                self._load_file(yaml_file)
                self.logger.info(f"  Loaded: {yaml_file.name}")

        # If a single file is passed, load just that file
        elif flows_path.is_file():
            self._load_file(flows_path)

        else:
            raise FileNotFoundError(f"Flows file or directory not found: {flows_file}")

    def _add_flow_if_unique(self, new_flow: Dict, source_file: Path, is_top_level: bool = False):
        flow_id = new_flow.get('id')
        if not flow_id:
            raise FlowDefinitionError(f"Attempted to add a flow without 'id' from {source_file.name}.")

        if any(f['id'] == flow_id for f in self.flows):
            source_context = "top-level" if is_top_level else "'flows' key"
            self.logger.warning(f"Duplicate flow ID '{flow_id}' found in {source_file.name} ({source_context}). Skipping.")
        else:
            self.flows.append(new_flow)
            source_context = "top-level" if is_top_level else "'flows' key"
            self.logger.info(f"Appended new {source_context} flow '{flow_id}' from {source_file.name}.")

    def _load_file(self, file_path: Path):
        """Load a single YAML file and merge into existing flows/solutions"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data:
            return

        # Handle new format with top-level 'steps'
        if 'steps' in data and isinstance(data['steps'], list):
            flow_id = data.get('id') or file_path.stem # Use explicit ID if present, otherwise filename
            new_flow = {
                'id': flow_id,
                'name': data.get('name') or flow_id.replace('_', ' ').title(),
                'description': data.get('description') or f"[AUTO-GENERATED] Troubleshooting guide for '{flow_id.replace('_', ' ').title()}' from {file_path.name}. Please add a specific 'description' in the YAML for better user experience.",
                'steps': data['steps']
            }
            self._add_flow_if_unique(new_flow, file_path, is_top_level=True)

        # Merge flows from 'flows' key, avoiding duplicates
        flows_from_key = data.get('flows', [])
        for flow_from_key in flows_from_key:
            if 'id' not in flow_from_key:
                raise FlowDefinitionError(
                    f"Flow without 'id' found in 'flows' key in {file_path.name}. "
                    "All flows must have a unique 'id'. Consider updating to the new top-level 'steps' format "
                    "or ensuring each flow under 'flows' has a unique 'id'."
                )
            self._add_flow_if_unique(flow_from_key, file_path, is_top_level=False)

        # Merge solutions - check for duplicate IDs
        new_solutions = data.get('solutions', [])
        for s in new_solutions:
            sol_id = s['id']
            if sol_id in self.solutions:
                self.logger.warning(f"  WARNING: Duplicate solution ID '{sol_id}' in {file_path.name} - overwriting")
            self.solutions[sol_id] = Solution(**s)

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

def load_engine(flows_file: str = 'data') -> TroubleshootingEngine:
    """
    Helper function to load and validate a troubleshooting engine

    Args:
        flows_file: Path to YAML flows file or directory

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
