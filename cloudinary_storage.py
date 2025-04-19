import os
import logging
import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.utils import cloudinary_url

logger = logging.getLogger(__name__)

# Check if Cloudinary credentials are available
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

# List of allowed file extensions
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'webm'}

class CloudinaryStorage:
    def __init__(self):
        self.is_configured = False
        if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
            cloudinary.config(
                cloud_name=CLOUDINARY_CLOUD_NAME,
                api_key=CLOUDINARY_API_KEY,
                api_secret=CLOUDINARY_API_SECRET,
                secure=True
            )
            self.is_configured = True
            logger.info("Cloudinary client initialized successfully")
        else:
            logger.warning("Cloudinary credentials not found, file uploads will be disabled")

    def is_allowed_file(self, filename):
        """Check if the file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def get_file_type(self, filename):
        """Determine if file is image or video based on extension"""
        extension = filename.rsplit('.', 1)[1].lower()
        if extension in ['jpg', 'jpeg', 'png', 'gif']:
            return 'image'
        elif extension in ['mp4', 'mov', 'webm']:
            return 'video'
        return None

    def upload_file(self, file_data, folder="pinspire_uploads", public_id=None, resource_type="auto"):
        """
        Upload a file to Cloudinary
        
        Args:
            file_data: The file data
            folder: Folder in Cloudinary to store the file
            public_id: Custom public ID for the file (optional)
            resource_type: Resource type ('image', 'video', or 'auto')
            
        Returns:
            Tuple of (file_url, file_type) or (None, None) if upload failed
        """
        if not self.is_configured:
            logger.error("Cloudinary not configured, cannot upload file")
            return None, None
            
        try:
            # Create upload options
            options = {
                'folder': folder,
                'resource_type': resource_type
            }
            
            if public_id:
                options['public_id'] = public_id
                
            # Upload the file
            logger.info(f"Uploading file to Cloudinary, resource_type={resource_type}")
            response = cloudinary.uploader.upload(file_data, **options)
            
            # Get the public URL
            file_url = response['secure_url']
            
            # Determine file type based on resource_type in response
            file_type = 'image' if response.get('resource_type') == 'image' else 'video'
            
            logger.info(f"File uploaded successfully to Cloudinary: {file_url}")
            return file_url, file_type
            
        except Exception as e:
            logger.error(f"Error uploading file to Cloudinary: {str(e)}")
            return None, None
            
    def delete_file(self, public_id, resource_type="image"):
        """
        Delete a file from Cloudinary
        
        Args:
            public_id: The public ID of the file to delete
            resource_type: Resource type ('image', 'video', or 'raw')
            
        Returns:
            Boolean indicating success or failure
        """
        if not self.is_configured:
            logger.error("Cloudinary not configured, cannot delete file")
            return False
            
        try:
            # Extract public_id from URL if a full URL was provided
            if public_id.startswith('http'):
                # Example: https://res.cloudinary.com/cloud_name/image/upload/v1234567890/folder/filename.jpg
                # Extract: folder/filename
                parts = public_id.split('/')
                if 'upload' in parts:
                    upload_index = parts.index('upload')
                    # Skip the version segment v1234567890
                    public_id = '/'.join(parts[upload_index + 2:])
                    # Remove file extension
                    public_id = public_id.rsplit('.', 1)[0] if '.' in public_id else public_id
            
            response = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
            
            if response.get('result') == 'ok':
                logger.info(f"File deleted successfully from Cloudinary: {public_id}")
                return True
            else:
                logger.error(f"Failed to delete file from Cloudinary: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting file from Cloudinary: {str(e)}")
            return False

# Create a singleton instance
cloudinary_storage = CloudinaryStorage()