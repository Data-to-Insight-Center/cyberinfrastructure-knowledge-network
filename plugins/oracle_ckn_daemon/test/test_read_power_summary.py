import unittest
import json
from oracle_ckn_daemon.power_processor import PowerProcessor
class TestPowerProcessor(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.summary_file_path = '/Users/swithana/git/d2i/icicle-ckn/oracle_ckn_daemon/examples/power_summary_report.json'
        self._power_processor = PowerProcessor(self.summary_file_path, None, "test-topic", 'test-experiment')

    def test_get_power_summary(self):

        with open(self.summary_file_path, 'r') as file:
            test_data = json.load(file)

        # Calculate expected totals
        expected_total_cpu_consumption = sum(
            plugin["cpu_power_consumption"] for plugin in test_data["plugin power summary report"])
        expected_total_gpu_consumption = sum(
            plugin["gpu_power_consumption"] for plugin in test_data["plugin power summary report"])

        # Expected flattened event
        expected_flattened_event = {
            'image_generating_plugin_cpu_power_consumption': 2.6314074074074068,
            'image_generating_plugin_gpu_power_consumption': 0.07603703703703703,
            'power_monitor_plugin_cpu_power_consumption': 2.5915555555555554,
            'power_monitor_plugin_gpu_power_consumption': 0.07137037037037038,
            'image_scoring_plugin_cpu_power_consumption': 2.5690384615384616,
            'image_scoring_plugin_gpu_power_consumption': 0.08219230769230768,
            'total_cpu_power_consumption': expected_total_cpu_consumption,
            'total_gpu_power_consumption': expected_total_gpu_consumption,
            'experiment_id': 'test-experiment',
        }

        # Call the function and get the result
        result = self._power_processor.get_power_summary()

        # Assert that the result matches the expected output
        self.assertEqual(result, expected_flattened_event)

        print(result)

if __name__ == "__main__":
    unittest.main()