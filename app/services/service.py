from typing import cast
from flask import Flask, Blueprint, request, jsonify
from abc import ABC, abstractmethod

class Service(ABC):
    """
    Abstract base class for defining services.
    Subclasses must implement the create_service method to define their service logic.
    
    Attributes:
        _service (any): The service instance.
        
    Properties:
        settings (WavvyAPI): Access to the WavvyAPI settings from the current app.
        service (any): The service instance.
    """
    
    def __init__(self, app: Flask = None):
        self._settings = app.settings if app is not None else None
        self._supabase = app.supabase if app is not None else None
        if app is not None:
            with app.app_context():
                self._service = self.create_service()
        else:
            raise RuntimeError("Service must be initialized within an app context.")
        
    @property
    def settings(self):
        return self._settings
    
    @property
    def db(self):
        return self._supabase
    
    @property
    def service(self):
        return self._service
        
    @abstractmethod
    def create_service(self):
        raise NotImplementedError("Subclasses must implement create_service method.")