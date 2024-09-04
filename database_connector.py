import os
from google_cloud_secret_manager import access_secret
from google.cloud.sql.connector import Connector, IPTypes
import pg8000


def connect_with_connector() -> pg8000.Connection:
    """
    Initializes a connection pool for a Cloud SQL instance of Postgres.

    Uses the Cloud SQL Python Connector package.
    """

    instance_connection_name = access_secret("INSTANCE_CONNECTION_NAME")
    db_user = access_secret("DB_USER")
    db_pass = access_secret("DB_PASS")
    db_name = access_secret("DB_NAME")

    #ip_type = IPTypes.PRIVATE if access_secret("PRIVATE_IP") else IPTypes.PUBLIC

    try:
        access_secret("PRIVATE_IP")
        ip_type = IPTypes.PRIVATE

    except:
        ip_type = IPTypes.PUBLIC

    # initialize Cloud SQL Python Connector object
    connector = Connector()

    conn = connector.connect(
        instance_connection_name,
        "pg8000",
        user=db_user,
        password=db_pass,
        db=db_name,
        ip_type=ip_type,
    )
    return conn
