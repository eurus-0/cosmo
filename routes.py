import os
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

from app import app, db
from models import User, Post, Collection, Save
# Import our new Cloudinary storage
from cloudinary_storage import cloudinary_storage

# Configure logging
logger = logging.getLogger(__name__)

# Check if Cloudinary is configured
UPLOADS_ENABLED = cloudinary_storage.is_configured

# Routes
from flask import render_template
from models import Post

def init_routes(app):
    @app.route('/')
    def index():
        posts = Post.query.order_by(Post.created_at.desc()).all()
        return render_template('index.html', posts=posts, title="Home")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html', title="Login")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validate input
        if not username or not email or not password:
            flash('All fields are required.')
            return render_template('register.html', title="Register")
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.')
            return render_template('register.html', title="Register")
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already taken.')
            return render_template('register.html', title="Register")
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return render_template('register.html', title="Register")
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        # Add user to database
        db.session.add(user)
        db.session.commit()
        
        # Create a default collection for the user
        default_collection = Collection(
            name="Saved",
            description="Your saved pins",
            user_id=user.id
        )
        db.session.add(default_collection)
        db.session.commit()
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html', title="Register")

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    collections = Collection.query.filter_by(user_id=user.id).all()
    
    return render_template('profile.html', user=user, posts=posts, collections=collections, title=f"{user.username}'s Profile")

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    # Check if Cloudinary is configured
    if not UPLOADS_ENABLED:
        flash('File uploads are temporarily disabled. Please check back later.')
        return render_template('upload.html', title="Upload", uploads_disabled=True)
    
    if request.method == 'POST':
        title = request.form.get('title', '')
        description = request.form.get('description', '')
        
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and cloudinary_storage.is_allowed_file(file.filename):
            try:
                # Generate a unique ID for the file
                unique_id = str(uuid.uuid4())
                
                # Read file data
                file_data = file.read()
                
                logger.info(f"Uploading file to Cloudinary: {file.filename}, size: {len(file_data)} bytes")
                
                # Upload to Cloudinary
                file_url, file_type = cloudinary_storage.upload_file(
                    file_data,
                    folder="pinspire",
                    public_id=unique_id
                )
                
                if file_url:
                    # Create new post
                    new_post = Post(
                        title=title,
                        description=description,
                        file_url=file_url,
                        file_type=file_type,
                        user_id=current_user.id
                    )
                    
                    db.session.add(new_post)
                    db.session.commit()
                    
                    logger.info(f"Post created successfully with file: {file_url}")
                    flash('Post uploaded successfully!')
                    return redirect(url_for('profile', username=current_user.username))
                else:
                    logger.error(f"File upload to Cloudinary failed")
                    flash('Failed to upload file. Storage service is currently unavailable.')
                    return redirect(request.url)
            except Exception as e:
                logger.error(f"Error during file upload: {str(e)}")
                flash('An error occurred during file upload. Please try again.')
                return redirect(request.url)
        else:
            flash('File type not allowed')
            return redirect(request.url)
    
    return render_template('upload.html', title="Upload", uploads_disabled=False)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # For now, we'll redirect to the home page with the modal pre-opened
    # The actual implementation will use JavaScript to open the modal
    return redirect(url_for('index', modal_post_id=post_id))

@app.route('/api/post/<int:post_id>')
def get_post(post_id):
    post = Post.query.get_or_404(post_id)
    author = User.query.get(post.user_id)
    
    # Count saves
    save_count = Save.query.filter_by(post_id=post_id).count()
    
    # Check if current user has saved this post
    saved = False
    if current_user.is_authenticated:
        saved = Save.query.filter(
            Save.post_id == post_id,
            Save.collection_id.in_([c.id for c in current_user.collections])
        ).first() is not None
    
    post_data = {
        'id': post.id,
        'title': post.title,
        'description': post.description,
        'file_url': post.file_url,
        'file_type': post.file_type,
        'created_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'author': {
            'id': author.id,
            'username': author.username,
            'profile_image_url': author.profile_image_url
        },
        'save_count': save_count,
        'saved': saved
    }
    
    return jsonify(post_data)

@app.route('/api/save/<int:post_id>', methods=['POST'])
@login_required
def save_post(post_id):
    post = Post.query.get_or_404(post_id)
    collection_id = request.json.get('collection_id')
    
    # If no collection is specified, use the user's default "Saved" collection
    if not collection_id:
        default_collection = Collection.query.filter_by(
            user_id=current_user.id, 
            name="Saved"
        ).first()
        
        if not default_collection:
            # Create default collection if it doesn't exist
            default_collection = Collection(
                name="Saved",
                description="Your saved pins",
                user_id=current_user.id
            )
            db.session.add(default_collection)
            db.session.commit()
            
        collection_id = default_collection.id
    
    # Check if the collection belongs to the current user
    collection = Collection.query.get_or_404(collection_id)
    if collection.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if the post is already saved in this collection
    existing_save = Save.query.filter_by(
        post_id=post_id,
        collection_id=collection_id
    ).first()
    
    if existing_save:
        return jsonify({'error': 'Post already saved to this collection'}), 400
    
    # Save the post to the collection
    new_save = Save(
        post_id=post_id,
        collection_id=collection_id
    )
    
    db.session.add(new_save)
    db.session.commit()
    
    return jsonify({'success': True}), 200

@app.route('/api/unsave/<int:post_id>', methods=['POST'])
@login_required
def unsave_post(post_id):
    collection_id = request.json.get('collection_id')
    
    # If no collection specified, find all saves for this post by the current user
    if not collection_id:
        saves = Save.query.join(Collection).filter(
            Save.post_id == post_id,
            Collection.user_id == current_user.id
        ).all()
    else:
        # Verify the collection belongs to the current user
        collection = Collection.query.get_or_404(collection_id)
        if collection.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
            
        saves = Save.query.filter_by(
            post_id=post_id,
            collection_id=collection_id
        ).all()
    
    if not saves:
        return jsonify({'error': 'Post not saved to specified collection'}), 404
    
    # Remove all found saves
    for save in saves:
        db.session.delete(save)
    
    db.session.commit()
    
    return jsonify({'success': True}), 200

@app.route('/collection/<int:collection_id>')
def view_collection(collection_id):
    collection = Collection.query.get_or_404(collection_id)
    
    # Get all posts in this collection
    posts = Post.query.join(Save).filter(
        Save.collection_id == collection_id
    ).order_by(Post.created_at.desc()).all()
    
    return render_template(
        'collection.html', 
        collection=collection,
        posts=posts,
        title=collection.name
    )

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('index'))
    
    # Search for posts matching the query in title or description
    posts = Post.query.filter(
        (Post.title.ilike(f'%{query}%') | Post.description.ilike(f'%{query}%'))
    ).order_by(Post.created_at.desc()).all()
    
    # Search for users matching the query in username
    users = User.query.filter(User.username.ilike(f'%{query}%')).all()
    
    return render_template(
        'search.html',
        query=query,
        posts=posts,
        users=users,
        title=f"Search: {query}"
    )
