from typing import cast
from flask import Flask, Blueprint, request, jsonify
from abc import ABC, abstractmethod
    
class Routes(ABC):
    """
    Abstract base class for defining API routes.
    Subclasses must implement the create_blueprint method to define their routes.
    
    Attributes:
        _bp (Blueprint): The Flask Blueprint instance for the routes.
        
    Properties:
        settings (WavvyAPI): Access to the WavvyAPI settings from the current app.
        blueprint (Blueprint): The Blueprint instance containing the defined routes.
    """
    
    def __init__(self, app: Flask = None):
        self._settings = app.settings 
        self._db = app.supabase
        self._bp = None
        
    @property
    def settings(self):
        return self._settings
    
    @property
    def db(self):
        return self._db
        
    @property
    def blueprint(self) -> Blueprint:
        return self._bp
        
    @abstractmethod
    def create_blueprint(self, app: Flask) -> Blueprint:
        raise NotImplementedError("Subclasses must implement create_blueprint method.")
        