import sys
import requests
import argparse
from typing import List, Tuple
from passlib.context import CryptContext
from webdev.database import get_database, UserInDB, create_user, get_user

# Initialize Password Context for hashing and verifying
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def register_user(base_url, username: str, password: str):
    response = requests.post(f"{base_url}/register/", json={"username": username, "password": password})
    return response.json()

def get_access_token(base_url, username: str, password: str):
    data = {"username": username, "password": password}
    response = requests.post(f"{base_url}/token", data=data)
    return response.json()['access_token']

def upload_file(base_url, token: str, file_content: str):
    # Correctly format the files parameter to include the file content and filename
    files = {'files': ('test.txt', file_content, 'text/plain')}
    headers = {"Authorization": f"Bearer {token}"}

    # Make the POST request with the files and headers
    response = requests.post(f"{base_url}/uploadfiles/", files=files, headers=headers)
    return response.json()

def upload_files(base_url, token: str, files_content: list):
    """
    Upload multiple files to the FastAPI server.

    :param base_url: The base URL where the FastAPI app is running.
    :param token: The access token for authorization.
    :param files_content: A list of tuples, each containing the filename and the file content.
    """
    # The 'files' parameter is a list of tuples, each representing a file.
    # Each tuple is in the format: ('files', (filename, content, 'MIME-Type'))
    files = [('files', (filename, content, 'text/plain')) for filename, content in files_content]

    headers = {"Authorization": f"Bearer {token}"}

    # Make the POST request with the files and headers
    response = requests.post(f"{base_url}/uploadfiles/", files=files, headers=headers)
    return response.json()

def upload_multiple_files(base_url, token: str, files_content: List[Tuple[str, str]]):
    files = [('files', (file_name, content)) for file_name, content in files_content]
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{base_url}/uploadfiles/", files=files, headers=headers)
    return response.json()

def get_user_statistics(base_url: str, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/user_stats", headers=headers)
    if response.headers.get('Content-Type') == 'application/json':
        # Handle JSON response
        return response.json()
    return response.content.decode()

def retrieve_user_data(base_url: str, token: str, filename: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/retrieve/{filename}", headers=headers)
    if response.headers.get('Content-Type') == 'application/json':
        # Handle JSON response
        return response.json()
    elif response.status_code == 200:
        # Handle file response, save to a file, or process as needed
        file_content = response.content
        # Example: save to a local file
        with open(filename, 'wb') as f:
            f.write(file_content)
        return {"success": True, "message": "File downloaded successfully."}
    else:
        return {"success": False, "message": f"Failed to retrieve file with error: {response.content.decode()}"}

# Add some fake users to the database
def test_create_fake_users():
    redis_db = get_database()

    # Create a new user
    fake_user_jane = UserInDB(
        username="janedoe",
        hashed_password=pwd_context.hash("password123"),
        seed="b6825ec6168f72e90b1244b1d2307433ad8394ad65b7ef4af10966bc103a39bf",
        wallet_name="janedoe",
        wallet_hotkey="default",
        wallet_mnemonic="ocean bean until sauce near place labor admit dismiss long asthma tunnel"
    )
    create_user(fake_user_jane)

    # Retrieve the user
    user = get_user("janedoe")
    assert user == fake_user_jane, "User doesn't match expected"

    fake_user_john = UserInDB(
            username="johndoe", 
            hashed_password=pwd_context.hash("example"), 
            seed="a6825ec6168f72e90b1244b1d2307433ad8394ad65b7ef4af10966bc103a39ae", 
            wallet_name = 'johndoe',   # should be equivalent to username for consistency
            wallet_hotkey = 'default', # can be default
            wallet_mnemonic = 'family bean until sauce near place labor admit dismiss long asthma tunnel' 
        )

    create_user(fake_user_john)
    user = get_user("johndoe")
    assert user == fake_user_john, "User doesn't match expected"

def get_user_metadata(base_url, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(f"{base_url}/user_data", headers=headers).json()

def get_hotkeys_by_cid(base_url, token: str, cid: str):
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(f"{base_url}/hotkeys/{cid}", headers=headers).json()


def main():
    parser = argparse.ArgumentParser(description="Test FastAPI application")
    parser.add_argument('--host', type=str, default='localhost', help='Host where the FastAPI app is running')
    parser.add_argument('--port', type=str, default='8001', help='Port on which the FastAPI app is running')
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"

    username = "janedoe"
    password = "password123"
    file_content = "This is a test string."

    print("Registering user...")
    register_response = register_user(base_url, username, password)
    print(register_response)

    print("Getting access token...")
    token = get_access_token(base_url, username, password)
    print("Access Token:", token)

    print("Uploading file...")
    resp = upload_file(base_url, token, file_content)
    if len(resp) > 1:
        cid, hotkeys = resp
        print(cid, hotkeys)
    else:
        print(resp)

    print("Retrieving file...")
    response = retrieve_user_data(base_url, token, 'test.txt')
    print(response)

    print("Getting user metadata...")
    user_metadata = get_user_metadata(base_url, token)
    print("User Metadata:", user_metadata)

    print("Get hotkeys by CID...")
    hotkeys = get_hotkeys_by_cid(base_url, token, cid)
    print("Hotkeys:", hotkeys)

    # TODO: add tests for adding multiple files per user and checking the storage/size is correct

if __name__ == "__main__":
    main()
