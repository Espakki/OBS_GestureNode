import sys
from pathlib import Path

# Permite `from core...` / `from engine...` sem instalar o projeto como pacote.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
