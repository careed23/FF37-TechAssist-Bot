import unittest
from unittest.mock import MagicMock, patch, mock_open
import yaml
import logging
from pathlib import Path

# Assume TroubleshootingEngine is importable from its path
from techassist.flow_engine import TroubleshootingEngine, FlowDefinitionError

class TestTroubleshootingEngine(unittest.TestCase):

    @patch("techassist.flow_engine.TroubleshootingEngine.__init__", return_value=None)
    def setUp(self, mock_init):
        # Suppress actual logging during tests
        logging.disable(logging.CRITICAL)
        # Create an instance by bypassing the original __init__
        self.engine = TroubleshootingEngine.__new__(TroubleshootingEngine)
        self.engine.logger = MagicMock() # Directly assign a MagicMock to the logger
        self.engine.flows = []
        self.engine.solutions = {}


    def tearDown(self):
        logging.disable(logging.NOTSET)

    @patch("techassist.flow_engine.Path.is_file")
    @patch("builtins.open", new_callable=mock_open, read_data="id: test_flow\nname: Test Flow\ndescription: A test flow\nsteps:\n  - step1: {}")
    def test_load_file_top_level_steps(self, mock_file, mock_is_file):
        mock_is_file.return_value = True
        self.engine._load_file(Path("dummy_path.yaml"))
        self.assertEqual(len(self.engine.flows), 1)
        self.assertEqual(self.engine.flows[0]["id"], "test_flow")
        self.assertEqual(self.engine.flows[0]["name"], "Test Flow")
        self.assertIn("step1", self.engine.flows[0]["steps"][0])

    @patch("techassist.flow_engine.Path.is_file")
    @patch("builtins.open", new_callable=mock_open, read_data="flows:\n  - id: flow_key_test\n    name: Flow Key Test\n    steps:\n      - stepA: {}")
    def test_load_file_from_flows_key(self, mock_file, mock_is_file):
        mock_is_file.return_value = True
        self.engine._load_file(Path("dummy_path.yaml"))
        self.assertEqual(len(self.engine.flows), 1)
        self.assertEqual(self.engine.flows[0]["id"], "flow_key_test")
        self.assertEqual(self.engine.flows[0]["name"], "Flow Key Test")
        self.assertIn("stepA", self.engine.flows[0]["steps"][0])

    @patch("techassist.flow_engine.Path.is_file")
    @patch("builtins.open", new_callable=mock_open, read_data="id: test_flow\nname: Test Flow\ndescription: A test flow\nsteps:\n  - step1: {}")
    def test_load_file_duplicate_top_level_id(self, mock_file, mock_is_file):
        mock_is_file.return_value = True

        self.engine.flows.append({"id": "test_flow", "name": "Existing Flow", "steps": []})
        self.engine._load_file(Path("test_file.yaml"))

        self.assertEqual(len(self.engine.flows), 1)
        self.engine.logger.warning.assert_called_with("Flow with ID 'test_flow' from top-level in test_file.yaml already exists. Skipping to avoid duplication.")

    @patch("techassist.flow_engine.Path.is_file")
    @patch("builtins.open", new_callable=mock_open, read_data="flows:\n  - id: duplicate_id\n    name: Duplicate Flow\n    steps: []")
    def test_load_file_duplicate_id_in_flows_key(self, mock_file, mock_is_file):
        mock_is_file.return_value = True

        self.engine.flows.append({"id": "duplicate_id", "name": "Existing Flow", "steps": []})
        self.engine._load_file(Path("test_file.yaml"))

        self.assertEqual(len(self.engine.flows), 1)
        self.engine.logger.warning.assert_called_with("Flow with ID 'duplicate_id' from 'flows' key in test_file.yaml already exists. Skipping to avoid duplication.")

    @patch("techassist.flow_engine.Path.is_file")
    @patch("builtins.open", new_callable=mock_open, read_data="flows:\n  - name: Flow without ID\n    steps: []")
    def test_load_file_flow_without_id_in_flows_key(self, mock_file, mock_is_file):
        mock_is_file.return_value = True
        with self.assertRaises(FlowDefinitionError):
            self.engine._load_file(Path("test_file.yaml"))

        self.assertEqual(len(self.engine.flows), 0)

    @patch("techassist.flow_engine.Path.is_file", return_value=False)
    @patch("techassist.flow_engine.Path.is_dir", return_value=True)
    @patch("techassist.flow_engine.Path.glob", return_value=[])
    @patch("techassist.flow_engine.logging.getLogger") # Keep this patch for the separate engine instance
    def test_load_flows_from_dir_no_yaml_files(self, mock_get_logger, mock_glob, mock_is_dir, mock_is_file):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        with self.assertRaises(FileNotFoundError) as cm:
            # We need to create a new engine instance here to test the constructor's behavior
            TroubleshootingEngine(Path("dummy_dir"))
        self.assertIn("No YAML files found in directory", str(cm.exception))
        mock_logger.error.assert_called_with("No YAML files found in directory: dummy_dir")

if __name__ == "__main__":
    unittest.main()