import copy
import json
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

from engine.gesture_engine import GestureEngine
from ui.main_window import MainWindow


def run():
    app = QApplication([])

    with open("config.json", "r", encoding="utf-8") as file:
        config = json.load(file)

    config_test = copy.deepcopy(config)
    config_test["modo"] = "test"

    window_test = MainWindow(config_test)
    test_errors, test_warnings = window_test._validar_config_execucao()

    engine_test = GestureEngine(config_test)

    config_obs = copy.deepcopy(config)
    config_obs["modo"] = "obs"

    window_obs = MainWindow(config_obs)
    obs_errors, obs_warnings = window_obs._validar_config_execucao()

    engine_obs = GestureEngine(config_obs)

    print("UI_TEST_VALIDATION", isinstance(test_errors, list), isinstance(test_warnings, list))
    print("UI_OBS_VALIDATION", isinstance(obs_errors, list), isinstance(obs_warnings, list))
    print("ENGINE_TEST_INIT", bool(engine_test.camera and engine_test.detector))
    print("ENGINE_OBS_INIT", bool(engine_obs.camera and engine_obs.detector))

    window_test.close()
    window_obs.close()
    app.quit()


if __name__ == "__main__":
    run()
