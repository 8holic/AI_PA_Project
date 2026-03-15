import os
import importlib

def load_modules(app):

    module_folder = "modules"

    if not os.path.exists(module_folder):
        return

    for name in os.listdir(module_folder):

        path = os.path.join(module_folder, name)

        if os.path.isdir(path):

            try:
                module = importlib.import_module(
                    f"modules.{name}.module"
                )

                if hasattr(module, "setup"):
                    module.setup(app)

                print("Loaded module:", name)

            except Exception as e:
                print("Failed loading:", name, e)