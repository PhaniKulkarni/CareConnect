import os
from dotenv import load_dotenv
from snowflake.connector import connect
from snowflake.snowpark import Session
from snowflake.core import Root

class SnowflakeConnection:
    def __init__(self):
        load_dotenv()
        self.user = os.getenv("SNOWFLAKE_USER")
        self.password = os.getenv("SNOWFLAKE_PASSWORD")
        self.account = os.getenv("SNOWFLAKE_ACCOUNT")
        self.warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
        self.database = os.getenv("SNOWFLAKE_DATABASE", "MEDICAL_CORTEX_SEARCH_APP")
        self.schema = os.getenv("SNOWFLAKE_SCHEMA", "DATA")
        
        self.connection = None
        self.session = None
        self.root = None

    def create_session(self) -> Session:
        """Create Snowpark session"""
        connection_parameters = {
            "account": self.account,
            "user": self.user,
            "password": self.password,
            "warehouse": self.warehouse,
            "database": self.database,
            "schema": self.schema
        }
        return Session.builder.configs(connection_parameters).create()

    def connect(self):
        """Establish connection to Snowflake"""
        try:
            # Create Snowpark session
            self.session = self.create_session()
            
            # Create regular connection
            self.connection = connect(
                user=self.user,
                password=self.password,
                account=self.account,
                warehouse=self.warehouse,
                database=self.database,
                schema=self.schema
            )
            
            # Initialize Root object
            self.root = Root(self.session)
            return True
        except Exception as e:
            print(f"Error connecting to Snowflake: {str(e)}")
            return False

    def get_session(self):
        """Return active session"""
        if not self.session:
            self.connect()
        return self.session

    def get_root(self):
        """Return root object"""
        if not self.root:
            self.connect()
        return self.root

    def close(self):
        """Close Snowflake connection"""
        if self.session:
            self.session.close()
        if self.connection:
            self.connection.close()