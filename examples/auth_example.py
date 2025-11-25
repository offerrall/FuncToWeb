from func_to_web import run

def get_secret_data():
    """This function requires login."""
    return "Access Granted: Here is the secret data."

def set_secret_data(data: str):
    """This function sets secret data."""
    return "Access Granted: Secret data has been set."

if __name__ == "__main__":
    users_auth = {
        "admin": "1234",  # username: password (Ensure to use secure and unique credentials in production)
        "user": "abcd"
    }
    run(
        [get_secret_data, set_secret_data],
        auth=users_auth, # Use os.getenv to fetch credentials securely in production
        secret_key=None, # You can set a secret key for session persistence or leave it as None for random keys
        port=8080
    )