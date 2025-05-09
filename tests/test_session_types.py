# to be able to use modules from other files
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))