"""
Test 03: DigitalOcean Spaces integration.

Tests S3-compatible object storage operations.
"""

import pytest
import tempfile
from pathlib import Path
from uuid import uuid4


class TestSpacesClient:
    """Test DigitalOcean Spaces client."""

    def test_spaces_module_imports(self):
        """Check that Spaces module can be imported."""
        from app.core.spaces import SpacesClient, get_spaces_client
        
        assert SpacesClient is not None
        assert callable(get_spaces_client)

    def test_spaces_client_methods(self):
        """Check that SpacesClient has required methods."""
        from app.core.spaces import SpacesClient
        
        required_methods = [
            "upload_file",
            "upload_fileobj",
            "download_file",
            "download_fileobj",
            "get_object_bytes",
            "exists",
            "delete",
            "list_objects",
            "get_public_url",
            "generate_presigned_url",
        ]
        
        for method in required_methods:
            assert hasattr(SpacesClient, method), f"SpacesClient should have {method} method"

    @pytest.mark.integration
    def test_spaces_upload_download(self, has_spaces_credentials):
        """Test uploading and downloading a file to/from Spaces."""
        if not has_spaces_credentials:
            pytest.skip("Spaces credentials not available")
        
        from app.core.spaces import get_spaces_client
        
        spaces = get_spaces_client()
        
        # Create a test file
        test_content = f"AgriPulse test file - {uuid4()}"
        test_key = f"test/pytest_{uuid4().hex[:8]}.txt"
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(test_content)
            local_path = Path(f.name)
        
        try:
            # Upload
            result = spaces.upload_file(
                local_path=local_path,
                s3_key=test_key,
                content_type="text/plain",
            )
            
            assert result["s3_key"] == test_key
            assert result["size_bytes"] > 0
            assert result["etag"] is not None
            
            # Check exists
            assert spaces.exists(test_key) is True
            
            # Download
            download_path = local_path.parent / f"download_{uuid4().hex[:8]}.txt"
            spaces.download_file(test_key, download_path)
            
            assert download_path.exists()
            assert download_path.read_text() == test_content
            
            # Get bytes
            content_bytes = spaces.get_object_bytes(test_key)
            assert content_bytes.decode() == test_content
            
            # Get public URL
            public_url = spaces.get_public_url(test_key)
            assert public_url.startswith("https://")
            assert test_key in public_url
            
            # Generate presigned URL
            presigned_url = spaces.generate_presigned_url(test_key, expires_in=60)
            assert presigned_url.startswith("https://")
            
        finally:
            # Cleanup
            local_path.unlink(missing_ok=True)
            if 'download_path' in locals():
                download_path.unlink(missing_ok=True)
            
            # Delete from Spaces
            spaces.delete(test_key)
            assert spaces.exists(test_key) is False

    @pytest.mark.integration
    def test_spaces_list_objects(self, has_spaces_credentials):
        """Test listing objects in Spaces."""
        if not has_spaces_credentials:
            pytest.skip("Spaces credentials not available")
        
        from app.core.spaces import get_spaces_client
        
        spaces = get_spaces_client()
        
        # List objects (may be empty)
        objects = spaces.list_objects(prefix="test/", max_keys=10)
        
        # Should return a list
        assert isinstance(objects, list)

    @pytest.mark.integration
    def test_spaces_upload_fileobj(self, has_spaces_credentials):
        """Test uploading a file-like object to Spaces."""
        if not has_spaces_credentials:
            pytest.skip("Spaces credentials not available")
        
        from app.core.spaces import get_spaces_client
        import io
        
        spaces = get_spaces_client()
        
        test_content = f"AgriPulse fileobj test - {uuid4()}"
        test_key = f"test/pytest_fileobj_{uuid4().hex[:8]}.txt"
        
        try:
            # Upload from file-like object
            file_obj = io.BytesIO(test_content.encode())
            result = spaces.upload_fileobj(
                file_obj=file_obj,
                s3_key=test_key,
                content_type="text/plain",
            )
            
            assert result["s3_key"] == test_key
            assert result["size_bytes"] > 0
            
            # Verify content
            content = spaces.get_object_bytes(test_key)
            assert content.decode() == test_content
            
        finally:
            spaces.delete(test_key)
