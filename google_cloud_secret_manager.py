from google.cloud import secretmanager

def access_secret(secret_name):
    client = secretmanager.SecretManagerServiceClient()
    project_id = "tutor-helper-432904"
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")