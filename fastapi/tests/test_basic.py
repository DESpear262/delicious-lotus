"""
Basic smoke tests for API routes
"""

def test_import_app():
    """Test that we can import the app"""
    from app.main import create_application
    app = create_application()
    assert app is not None

def test_import_schemas():
    """Test that schemas can be imported"""
    from app.models.schemas import GenerationRequest, CreateGenerationResponse
    assert GenerationRequest is not None
    assert CreateGenerationResponse is not None
