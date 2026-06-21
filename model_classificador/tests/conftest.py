"""Configuração compartilhada dos testes.

Garante que a raiz do projeto esteja no sys.path, permitindo importar os
módulos `ia.preprocess` e `ia.model_local` ao rodar o pytest de qualquer lugar.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
