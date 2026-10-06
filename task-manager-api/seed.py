"""Script para popular o banco com dados iniciais: python seed.py"""
from app import create_app
from database.seed import seed_data

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        counts = seed_data()
    print('Seed concluído com sucesso!')
    print(f"  {counts['users']} usuários")
    print(f"  {counts['categories']} categorias")
    print(f"  {counts['tasks']} tasks")
