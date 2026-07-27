"""Reexporta a configuracao centralizada (src/config) para o Streamlit.

Nao duplicamos a leitura de variaveis de ambiente aqui: pipeline e app
compartilham a MESMA fonte de verdade (src/config/settings.py).
"""

from src.config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
