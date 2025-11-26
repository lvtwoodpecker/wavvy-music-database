# app/core.py
from flask import Flask
from app.db.supabase_client import SupabaseClient
from supabase import Client
from .config import Settings
from app.api import WavvyAPIBlueprints
from app.services.register_services import APIServices


class WavvyAPI(Flask):
    """
    Custom Flask application class for the Wavvy backend.
    Holds the Supabase client and any app-level services.
    """

    def __init__(self, import_name, **kwargs):
        super().__init__(import_name, **kwargs)
        self._settings = Settings()
        self._supabase: Client = None
        self._services = None

    # --------- Settings ----------
    @property
    def settings(self) -> Settings:
        """Access the app's settings instance."""
        return self._settings

    # --------- Supabase ----------
    @property
    def supabase(self) -> Client:
        """Access the Supabase client."""
        if self._supabase is None:
            raise RuntimeError("Supabase client accessed before initialization.")
        return self._supabase
    
    @property
    def services(self) -> APIServices:
        """Access the app's API services instance."""
        return self._services

    def init_supabase(self) -> None:
        """Initialize the Supabase client on the app instance."""
        self._supabase = SupabaseClient.init_supabase(
            self._settings.SUPABASE_URL,
            self._settings.SUPABASE_SERVICE_KEY,
        )

    def init_services(self) -> None:
        """Initialize the API services on the app instance."""
        self._services = APIServices()
        
    # --------- Config ----------
    def init_config(self) -> None:
        """Initialize configuration settings."""
        self.config["SECRET_KEY"] = self._settings.SECRET_KEY
        self.config["ENV"] = self._settings.ENV

    # --------- Blueprints ----------
    def register_blueprints(self) -> None:
        """Register all blueprints for the app."""
        WavvyAPIBlueprints.register_blueprints(self) # pass self to the static method
