import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "your_secret_key_change_in_production")
    JWT_SECRET_KEY = os.environ.get(
        "JWT_SECRET_KEY", "your_jwt_secret_key_change_in_production"
    )
    JWT_ACCESS_TOKEN_EXPIRES = int(
        os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 3600)
    )  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = int(
        os.environ.get("JWT_REFRESH_TOKEN_EXPIRES", 2592000)
    )  # 30 days
    SUPABASE_URL = os.environ.get(
        "SUPABASE_URL", "https://raniqjkrinwyperxyhrw.supabase.co"
    )
    SUPABASE_KEY = os.environ.get(
        "SUPABASE_KEY",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJhbmlxamtyaW53eXBlcnh5aHJ3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjkyNjQzNSwiZXhwIjoyMDY4NTAyNDM1fQ.R3tVS--F889KMeCAD_iI3VGEqwQtsm_bAKIihw_vJ5s",
    )

    # Email Configuration
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "False").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "ainewshub89@gmail.com")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "xldaufoufokehnjl")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "ainewshub89@gmail.com")

    # OTP Configuration
    OTP_EXPIRY_MINUTES = int(os.environ.get("OTP_EXPIRY_MINUTES", 10))  # 10 minutes

    # Pinecone Configuration
    PINECONE_API_KEY = os.environ.get("pinecone_api_key")
    PINECONE_ENVIRONMENT = os.environ.get("pinecone_region")
    PINECONE_INDEX_NAME = os.environ.get("pinecone_index_name")

    # Together AI Configuration
    TOGETHER_AI_API_KEY = os.environ.get("TOGETHER_AI_API_KEY")
