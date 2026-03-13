import os
import importlib.util

MIGRATION_DIR = os.path.join(os.path.dirname(__file__), "migrations")

for file in sorted(os.listdir(MIGRATION_DIR)):
    if file.endswith(".py") and file != "__init__.py":
        path = os.path.join(MIGRATION_DIR, file)
        spec = importlib.util.spec_from_file_location("migration", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f"-- Running migration: {file}")
        module.run()