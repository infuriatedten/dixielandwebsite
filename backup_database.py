
import os
import subprocess
from datetime import datetime
from app import create_app

def backup_database():
    """Create a database backup"""
    app = create_app()
    
    with app.app_context():
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        
        if 'postgresql://' in db_uri:
            # PostgreSQL backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"backup_{timestamp}.sql"
            
            # Extract database URL components
            # Note: This is a basic implementation
            cmd = f"pg_dump {db_uri} > {backup_file}"
            
            try:
                subprocess.run(cmd, shell=True, check=True)
                print(f"Database backup created: {backup_file}")
                return backup_file
            except subprocess.CalledProcessError as e:
                print(f"Backup failed: {e}")
                return None

if __name__ == '__main__':
    backup_database()
