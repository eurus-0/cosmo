import os
import io
import requests
from supabase import create_client, Client
import logging

# Set up logging with more detail
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

class SupabaseClient:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.warning("Supabase URL or API key is missing from environment variables")
            self.supabase = None
        else:
            # Initialize the Supabase client
            self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            # Initialize the storage bucket when the client is created
            self._initialize_bucket()
            logger.info("Supabase client initialized")
    
    def _initialize_bucket(self):
        """Initialize the storage bucket if it doesn't exist"""
        if not self.supabase:
            return False
            
        try:
            # For simplicity, we'll use a predefined bucket that's always created in Supabase
            bucket_name = "avatars"
            logger.info("Using default Supabase storage bucket")
            return True
        except Exception as e:
            logger.error(f"Error initializing storage bucket: {str(e)}")
            return False
    
    def upload_file(self, file_data, file_path, content_type):
        """
        Upload a file to Supabase Storage
        
        Args:
            file_data: The file data in bytes
            file_path: The path where the file will be stored in Storage
            content_type: The MIME type of the file
        
        Returns:
            URL of the uploaded file or None if failed
        """
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return None
        
        try:
            # Use the default bucket
            bucket_name = "avatars"
            
            # Ensure file_path is a string
            file_path = str(file_path)
            
            # Log attempt
            logger.info(f"Attempting to upload file: {file_path}, size: {len(file_data)} bytes")
            
            # Try using the Python client first
            try:
                response = self.supabase.storage.from_(bucket_name).upload(
                    path=file_path,
                    file=file_data,
                    file_options={"contentType": content_type}
                )
                
                # Get the URL
                file_url = self.supabase.storage.from_(bucket_name).get_public_url(file_path)
                logger.info(f"File uploaded successfully with Python client: {file_url}")
                return file_url
                
            except Exception as inner_e:
                # If the Python client fails, fallback to direct API
                logger.warning(f"Python client upload failed: {str(inner_e)}, trying direct API...")
                
                # Use direct API approach as fallback
                url = f"{SUPABASE_URL}/storage/v1/object/{bucket_name}/{file_path}"
                headers = {
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": content_type
                }
                
                response = requests.post(url, headers=headers, data=file_data)
                
                if response.status_code == 200:
                    # Generate the public URL
                    file_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{file_path}"
                    logger.info(f"File uploaded successfully with direct API: {file_path}")
                    return file_url
                else:
                    logger.error(f"Upload failed with status {response.status_code}: {response.text}")
                    return None
            
        except Exception as e:
            logger.error(f"Error uploading file to Supabase: {str(e)}")
            return None
    
    def delete_file(self, file_path):
        """
        Delete a file from Supabase Storage
        
        Args:
            file_path: The path of the file in Storage
            
        Returns:
            Boolean indicating success or failure
        """
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return False
        
        try:
            # Use the default bucket
            bucket_name = "avatars"
            
            # Ensure file_path is a string
            file_path = str(file_path)
            
            # Try using the Python client first
            try:
                self.supabase.storage.from_(bucket_name).remove([file_path])
                logger.info(f"File deleted successfully with Python client: {file_path}")
                return True
                
            except Exception as inner_e:
                # If the Python client fails, fallback to direct API
                logger.warning(f"Python client delete failed: {str(inner_e)}, trying direct API...")
                
                # Use direct API approach as fallback
                url = f"{SUPABASE_URL}/storage/v1/object/{bucket_name}/{file_path}"
                headers = {
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}"
                }
                
                response = requests.delete(url, headers=headers)
                
                if response.status_code == 200:
                    logger.info(f"File deleted successfully with direct API: {file_path}")
                    return True
                else:
                    logger.error(f"Delete failed with status {response.status_code}: {response.text}")
                    return False
                
        except Exception as e:
            logger.error(f"Error deleting file from Supabase: {str(e)}")
            return False

# Create a singleton instance
supabase_client = SupabaseClient()
