import os
import shutil
from flask import Flask

def build():
    # Simple build script to satisfy Netlify
    dist_dir = 'dist'
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)

    # Create a dummy index.html in dist if it's empty,
    # though usually Netlify expects the app to run via functions or be static.
    # If this is a hybrid app, dist might need to contain the static assets.
    static_src = os.path.join('app', 'static')
    if os.path.exists(static_src):
        shutil.copytree(static_src, os.path.join(dist_dir, 'static'))

    print("Build completed successfully.")

if __name__ == "__main__":
    build()
