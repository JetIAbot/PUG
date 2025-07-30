import pytest
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

# Configurar variable de entorno TESTING
os.environ['TESTING'] = '1'

# Añadir el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def app():
    """Crear una instancia de la app para testing"""
    
    # Mock Firebase antes de importar la app
    with patch('firebase_admin.initialize_app'), \
         patch('firebase_admin.credentials.Certificate'), \
         patch('firebase_admin.firestore.client') as mock_firestore_client, \
         patch('firebase_admin._apps', []):
        
        # Configurar mock de firestore
        mock_db = MagicMock()
        mock_firestore_client.return_value = mock_db
        
        from src.app import create_app
        
        app = create_app({
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key',
            'CELERY_BROKER_URL': 'memory://',
            'CELERY_RESULT_BACKEND': 'cache+memory://'
        })
        
        with app.app_context():
            # Agregar mock db al contexto de la app
            app.config['mock_db'] = mock_db
            yield app

@pytest.fixture
def client(app):
    """Cliente de testing para hacer requests"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Runner para comandos CLI"""
    return app.test_cli_runner()

@pytest.fixture
def mock_firestore():
    """Mock para Firestore"""
    mock_db = MagicMock()
    
    # Configurar comportamiento por defecto del mock
    mock_collection = MagicMock()
    mock_document = MagicMock()
    mock_doc_ref = MagicMock()
    
    mock_db.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document
    mock_document.get.return_value = mock_doc_ref
    mock_doc_ref.exists = False
    
    return mock_db

@pytest.fixture
def mock_celery():
    """Mock para Celery"""
    mock_celery = MagicMock()
    mock_task = MagicMock()
    mock_task.id = 'test-task-id-123'
    mock_celery.send_task.return_value = mock_task
    return mock_celery
