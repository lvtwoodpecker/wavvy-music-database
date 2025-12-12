from abc import ABC, abstractmethod
from flask import Flask

class Service(ABC):
    """
    Base class for application services.

    Provides access to:
      - app settings
      - Supabase client (if available)
      - SQLAlchemy session factory (db_session_factory)
    """

    def __init__(self, app: Flask):
        if app is None:
            raise RuntimeError("Service must be initialized with an app instance.")

        # Keep a reference to the app if needed
        self._app = app

        # Core shared dependencies
        self._settings = app.settings            # Settings instance from WavvyAPI
        self._supabase = getattr(app, "supabase", None)
        self._db_session_factory = getattr(app, "db_session_factory", None)

        # NOTE: we do NOT auto-call create_service() here anymore.
        # Each subclass decides when/how to call create_service().

    # -------- Properties --------

    @property
    def settings(self):
        """Access application settings."""
        return self._settings

    @property
    def supabase(self):
        """Access Supabase client, if present."""
        return self._supabase

    @property
    def db_session_factory(self):
        """
        Access the SQLAlchemy SessionLocal factory.
        Services should use this to open DB sessions.
        """
        if self._db_session_factory is None:
            raise RuntimeError("db_session_factory is not configured on this app.")
        return self._db_session_factory

    @abstractmethod
    def create_service(self):
        """
        Subclasses implement this to initialize any internal sub-services
        or perform setup. They control when to call it (usually in __init__).
        """
        raise NotImplementedError("Subclasses must implement create_service().")
