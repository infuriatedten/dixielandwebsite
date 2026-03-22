import os
import shutil
from app import create_app

def build():
    app = create_app()
    # Logic to generate static files if needed, or just prepare the dist folder
    if not os.path.exists('dist'):
        os.makedirs('dist')

    # In a real app, this might use Flask-Static-Compress or similar
    # For now, we'll just ensure the directory exists as a placeholder
    print("Build completed successfully.")

if __name__ == "__main__":
    build()
