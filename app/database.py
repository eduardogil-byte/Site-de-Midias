from flask_sqlalchemy import SQLAlchemy

# inicializa o banco de dados vazio para os Models poderem importar sem importar todo o app
db = SQLAlchemy()