import os
import shutil

def build():
    print("Starting build process...")
    dist_dir = 'dist'
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)
    with open(os.path.join(dist_dir, 'index.html'), 'w') as f:
        f.write('Build completed successfully.')
    print("Build finished successfully.")

if __name__ == '__main__':
    build()
