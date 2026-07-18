from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.migrations import upgrade_database_to_head


if __name__ == "__main__":
	upgrade_database_to_head()
	print("Database migrations applied successfully.")

