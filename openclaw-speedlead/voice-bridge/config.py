"""
Voice Bridge configuration via environment variables.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Client
    client_id: str = "default"
    domain: str = "localhost"

    # Twilio
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str = ""

    # Deepgram
    deepgram_api_key: str

    # Cartesia
    cartesia_api_key: str
    cartesia_voice_id: str = "italian-male-professional"

    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    model_provider: str = "anthropic"

    # Supabase
    supabase_url: str
    supabase_service_key: str

    # OpenClaw
    openclaw_gateway_url: str = "http://openclaw:18789"

    class Config:
        env_file = ".env"
        case_sensitive = False
