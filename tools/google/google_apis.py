# import os
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build
# from google.oauth2.credentials import Credentials
# from google.auth.transport.requests import Request


# def create_service(client_secret_file, api_name, api_version, *scopes, prefix=''):
# 	"""
# 	Create a Google API service instance.

# 	Args:
# 		client_secret_file: Path to the client secret JSON file
# 		api_name: Name of the API service
# 		api_version: Version of the API
# 		scopes: Authorization scopes required by the API
# 		prefix: Optional prefix for token filename

# 	Returns:
# 		Google API service instance or None if creation failed
# 	"""
# 	CLIENT_SECRET_FILE = client_secret_file
# 	API_SERVICE_NAME = api_name
# 	API_VERSION = api_version
# 	SCOPES = [scope for scope in scopes[0]]

# 	creds = None
# 	working_dir = os.getcwd()
# 	token_dir = 'token-files'
# 	token_file = f'token_{API_SERVICE_NAME}_{API_VERSION}{prefix}.json'

# 	if not os.path.exists(os.path.join(working_dir, token_dir)):
# 		os.mkdir(os.path.join(working_dir, token_dir))

# 	if os.path.exists(os.path.join(working_dir, token_dir, token_file)):
# 		creds = Credentials.from_authorized_user_file(os.path.join(working_dir, token_dir, token_file), SCOPES)

# 	if not creds or not creds.valid:
# 		if creds and creds.expired and creds.refresh_token:
# 			creds.refresh(Request())
# 		else:
# 			flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
# 			creds = flow.run_local_server(port=0)
			
# 		with open(os.path.join(working_dir, token_dir, token_file), 'w') as token:
# 			token.write(creds.to_json())

# 	try:
# 		service = build(API_SERVICE_NAME, API_VERSION, credentials=creds, static_discovery=False)
# 		return service
# 	except Exception as e:
# 		os.remove(os.path.join(working_dir, token_dir, token_file))
# 		return None

import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


def create_service(
    client_secret_file,
    api_name,
    api_version,
    scopes,
    prefix="",
    token_dir=None,
    allow_interactive=True,
):
    """
    Create a Google API service instance.

    Key changes for MCP/Claude:
    - Token path is deterministic (defaults next to client_secret_file).
    - Can disable interactive OAuth (allow_interactive=False) so server won't hang.
    - Raises on failure instead of returning None.
    """
    client_secret_file = os.path.abspath(client_secret_file)

    # Deterministic token directory:
    # default: <dir-of-client-secret>/token-files
    base_dir = os.path.dirname(client_secret_file)
    if token_dir is None:
        token_dir = os.path.join(base_dir, "token-files")
    else:
        token_dir = os.path.abspath(token_dir)

    os.makedirs(token_dir, exist_ok=True)

    token_file = f"token_{api_name}_{api_version}{prefix}.json"
    token_path = os.path.join(token_dir, token_file)

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not allow_interactive:
                raise RuntimeError(
                    f"No valid token at {token_path}. Run interactive auth once locally to create it."
                )
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, scopes)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    service = build(api_name, api_version, credentials=creds, static_discovery=False)
    return service
