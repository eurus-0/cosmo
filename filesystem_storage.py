import os
import logging
import shutil
from urllib.parse import urljoin
from werkzeug.utils import secure_filename
from flask import url_for

logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'webm'}

# Create upload directory if it doesn't exist
os.makedirs(os.path.join(UPLOAD_FOLDER, 'images'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'videos'), exist_ok=True)

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename):
    """Determine if file is image or video based on extension"""
    extension = filename.rsplit('.', 1)[1].lower()
    if extension in ['jpg', 'jpeg', 'png', 'gif']:
        return 'image'
    elif extension in ['mp4', 'mov', 'webm']:
        return 'video'
    return None

def save_file(file_data, original_filename, custom_filename=None):
    """
    Save a file to the filesystem
    
    Args:
        file_data: The file data in bytes
        original_filename: The original filename
        custom_filename: Optional custom filename to use
        
    Returns:
        Tuple of (file_url, file_type) or (None, None) if failed
    """
    try:
        if not allowed_file(original_filename):
            logger.error(f"File type not allowed: {original_filename}")
            return None, None
            
        # Determine file type (image or video)
        file_type = get_file_type(original_filename)
        if not file_type:
            logger.error(f"Unknown file type: {original_filename}")
            return None, None
            
        # Create a secure filename
        secure_name = secure_filename(custom_filename or original_filename)
        
        # Choose subfolder based on file type
        subfolder = 'images' if file_type == 'image' else 'videos'
        file_path = os.path.join(UPLOAD_FOLDER, subfolder, secure_name)
        
        # Save the file
        with open(file_path, 'wb') as f:
            f.write(file_data)
            
        # Generate URL path relative to static folder
        url_path = f"/static/uploads/{subfolder}/{secure_name}"
        
        logger.info(f"File saved successfully: {file_path}")
        return url_path, file_type
        
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        return None, None

def delete_file(file_url):
    """
    Delete a file from the filesystem
    
    Args:
        file_url: The URL of the file to delete
        
    Returns:
        Boolean indicating success or failure
    """
    try:
        # Extract the file path from the URL
        # Example: /static/uploads/images/file.jpg -> static/uploads/images/file.jpg
        if file_url.startswith('/'):
            file_url = file_url[1:]
            
        file_path = os.path.join(os.getcwd(), file_url)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File deleted successfully: {file_path}")
            return True
        else:
            logger.warning(f"File does not exist: {file_path}")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return False