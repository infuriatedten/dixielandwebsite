import os
import shutil

def build():
    print("Starting build process...")
    dist_dir = 'dist'
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)

    # Netlify often needs these files in the publish directory
    with open(os.path.join(dist_dir, 'index.html'), 'w') as f:
        f.write('Build completed successfully.')

    open(os.path.join(dist_dir, '_headers'), 'a').close()
    open(os.path.join(dist_dir, '_redirects'), 'a').close()

    print("Build finished successfully.")

if __name__ == '__main__':
    build()
