import xml.etree.ElementTree as ET
from flask import current_app
import paramiko # For SCP
import os
import tempfile # For handling SSH keys from env vars if needed

# --- File Fetching ---
def _fetch_xml_content_scp(remote_host, remote_port, remote_user, remote_password, ssh_key_path, remote_filepath):
    """Fetches XML file content from a remote server using SCP."""
    ssh = None
    sftp = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # Auto-accept host key (consider security implications)

        pkey = None
        if ssh_key_path:
            # If ssh_key_path is actually the key content (e.g., from env var)
            if "-----BEGIN" in ssh_key_path:
                with tempfile.NamedTemporaryFile(delete=False) as tmp_key_file:
                    tmp_key_file.write(ssh_key_path.encode())
                    ssh_key_filepath_on_disk = tmp_key_file.name
                try:
                    pkey = paramiko.RSAKey.from_private_key_file(ssh_key_filepath_on_disk)
                finally:
                    os.remove(ssh_key_filepath_on_disk)
            else: # Assume it's a path to a key file
                 pkey = paramiko.RSAKey.from_private_key_file(ssh_key_path)

        current_app.logger.info(f"Attempting SCP connection to {remote_user}@{remote_host}:{remote_port} for {remote_filepath}")
        ssh.connect(remote_host, port=remote_port, username=remote_user, password=remote_password, pkey=pkey, timeout=10)

        sftp = ssh.open_sftp()
        with sftp.open(remote_filepath, 'r') as f:
            content = f.read().decode('utf-8') # Assuming UTF-8 encoding
        current_app.logger.info(f"Successfully fetched {remote_filepath} via SCP.")
        return content
    except Exception as e:
        current_app.logger.error(f"SCP Error fetching {remote_filepath} from {remote_host}: {e}")
        return None
    finally:
        if sftp:
            sftp.close()
        if ssh:
            ssh.close()

def _fetch_xml_content_local(local_filepath):
    """Fetches XML file content from a local path."""
    try:
        with open(local_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        current_app.logger.info(f"Successfully read {local_filepath} from local path.")
        return content
    except FileNotFoundError:
        current_app.logger.error(f"Local XML file not found: {local_filepath}")
        return None
    except Exception as e:
        current_app.logger.error(f"Error reading local XML file {local_filepath}: {e}")
        return None

# --- XML Parsing ---
def parse_server_status(xml_string):
    """Parses the livemap_dynamic.xml string and extracts server status information."""
    if not xml_string:
        return None
    try:
        root = ET.fromstring(xml_string)
        server_node = root # Assuming the root node is <Server> as per Lua script

        status_data = {
            'map_name': server_node.get('mapName'),
            'player_count': None, # Will be extracted from Players list if present
            'is_paused': server_node.get('paused') == 'true',
            'last_xml_update': server_node.get('lastUpdate'),
            'livemap_xml_version': server_node.get('version'),
            'livemap_mod_version': server_node.get('modVersion'),
            'game_version': server_node.get('gameVersion'),
            'error': None
        }

        # Extract player count (Count players where id is not serverUserId (1))
        players_node = server_node.find("Players")
        player_count = 0
        if players_node is not None:
            for player_elem in players_node.findall("Player"):
                player_id = player_elem.get("id")
                if player_id and player_id != "1": # Server user ID is 1 in the Lua
                    player_count += 1
        status_data['player_count'] = player_count

        # Potentially parse other elements like Weather, Vehicles, etc. in future phases
        # For now, focusing on the Server node attributes and player count.

        return status_data
    except ET.ParseError as e:
        current_app.logger.error(f"XML Parse Error: {e}")
        return {'error': f"XML parsing error: {e}"}
    except Exception as e:
        current_app.logger.error(f"Error parsing server status XML: {e}")
        return {'error': f"General error parsing XML: {e}"}


# --- Main Service Function ---
def get_live_server_status():
    """
    Fetches and parses the livemap_dynamic.xml to get current server status.
    Uses configuration to determine how to fetch the XML file.
    """
    access_method = current_app.config.get('LIVEMAP_XML_ACCESS_METHOD', 'LOCAL_PATH')
    xml_content = None

    if access_method == 'SCP':
        dynamic_xml_path = current_app.config.get('LIVEMAP_REMOTE_PATH_DYNAMIC')
        xml_content = _fetch_xml_content_scp(
            remote_host=current_app.config.get('LIVEMAP_REMOTE_HOST'),
            remote_port=current_app.config.get('LIVEMAP_REMOTE_PORT'),
            remote_user=current_app.config.get('LIVEMAP_REMOTE_USER'),
            remote_password=current_app.config.get('LIVEMAP_REMOTE_PASSWORD'),
            ssh_key_path=current_app.config.get('LIVEMAP_SSH_KEY_PATH'),
            remote_filepath=dynamic_xml_path
        )
    elif access_method == 'FTP':
        # TODO: Implement _fetch_xml_content_ftp using ftplib
        current_app.logger.warning("FTP access method for Livemap not yet implemented.")
        return {'error': "FTP access for Livemap is not implemented."}
    elif access_method == 'LOCAL_PATH':
        dynamic_xml_path = current_app.config.get('LIVEMAP_LOCAL_PATH_DYNAMIC')
        xml_content = _fetch_xml_content_local(dynamic_xml_path)
    else:
        current_app.logger.error(f"Invalid LIVEMAP_XML_ACCESS_METHOD: {access_method}")
        return {'error': f"Invalid Livemap XML access method configured: {access_method}"}

    if not xml_content:
        return {'error': "Failed to fetch Livemap XML data."}

    return parse_server_status(xml_content)

# Placeholder for fetching static data if needed in the future
# def get_livemap_static_data():
#     access_method = current_app.config.get('LIVEMAP_XML_ACCESS_METHOD', 'LOCAL_PATH')
#     static_xml_path = current_app.config.get('LIVEMAP_REMOTE_PATH_STATIC') if access_method != 'LOCAL_PATH' \
#                       else current_app.config.get('LIVEMAP_LOCAL_PATH_STATIC')
#     # ... similar fetching logic ...
#     # ... parsing logic for static data ...
#     pass
