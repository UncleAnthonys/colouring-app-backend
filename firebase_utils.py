"""
Firebase Storage utilities for Kids Colouring App
"""

import os
import json
import base64
import uuid
import firebase_admin
from firebase_admin import credentials, storage

_firebase_initialized = False


def init_firebase():
    """Initialize Firebase if not already done"""
    global _firebase_initialized
    
    if _firebase_initialized:
        return
    
    if not firebase_admin._apps:
        firebase_creds = os.environ.get("FIREBASE_CREDENTIALS_JSON")
        if firebase_creds:
            creds_dict = json.loads(firebase_creds)
            cred = credentials.Certificate(creds_dict)
        else:
            cred = credentials.ApplicationDefault()
        
        firebase_admin.initialize_app(cred, {
            'storageBucket': os.environ.get('FIREBASE_STORAGE_BUCKET', 'uncle-anthonys.firebasestorage.app')
        })
    
    _firebase_initialized = True


def upload_to_firebase(image_b64: str, folder: str = "generations") -> str:
    """Upload base64 image to Firebase Storage and return public URL"""
    init_firebase()
    
    image_bytes = base64.b64decode(image_b64)
    filename = f"{folder}/{uuid.uuid4()}.png"
    
    bucket = storage.bucket()
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type='image/png')
    blob.make_public()
    
    return blob.public_url
