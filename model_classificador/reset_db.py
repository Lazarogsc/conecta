import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db

with app.app_context():
    print("Deletando banco anterior...")
    db.drop_all()
    print("Recriando tabelas...")
    db.create_all()
    print("Banco recriado com sucesso!")
    print("Novas colunas: username, perfil_privado, tema")
