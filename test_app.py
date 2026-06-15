import unittest
from unittest.mock import patch
from app import create_app
from extensions import db

class EstoqueSmartTestCase(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('app._migrar_banco')
        self.mock_migrar = self.patcher.start()
        
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.patcher.stop()

    def test_acesso_dashboard_sem_login(self):
        response = self.client.get('/', follow_redirects=True)
        self.assertIn(b'login', response.request.path.encode())

    def test_cadastro_e_login(self):
        self.client.post('/auth/cadastro', data={
            'nome': 'Teste',
            'email': 'teste@teste.com',
            'senha': 'senha_segura',
            'confirmar': 'senha_segura',
            'cargo': 'admin',
            'nome_empresa': 'Empresa Teste'
        }, follow_redirects=True)

        response_login = self.client.post('/auth/login', data={
            'email': 'teste@teste.com',
            'senha': 'senha_segura'
        }, follow_redirects=True)
        
        self.assertEqual(response_login.status_code, 200)

if __name__ == '__main__':
    unittest.main()