"""
Configuration management for the security dashboard.
Handles loading and saving user settings from .env file or environment variables.
"""

import os
import json
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv, set_key


class Config:
    """Configuration manager for the dashboard."""
    
    # Configuration file paths
    #CONFIG_DIR = Path.home() / ".security_dashboard"
    CONFIG_DIR = Path.home() / ".ui_dashboard"
    ENV_FILE = CONFIG_DIR / ".env"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    
    # Default values
    DEFAULT_SERVER_URL = "http://localhost:5000"
    DEFAULT_API_KEY = ""
    
    @classmethod
    def init(cls):
        """Initialize configuration directory."""
        cls.CONFIG_DIR.mkdir(exist_ok=True)
        # Create .env file if it doesn't exist
        if not cls.ENV_FILE.exists():
            cls.ENV_FILE.write_text("")
    
    @classmethod
    def load(cls) -> dict:
        """
        Load configuration from .env file.
        
        Returns:
            Dictionary with keys: server_url, api_key
        """
        cls.init()
        
        # Load .env file if it exists
        if cls.ENV_FILE.exists():
            load_dotenv(cls.ENV_FILE)
        
        # Try environment variables first, then fall back to defaults
        server_url = os.getenv("SECURITY_SERVER_URL", cls.DEFAULT_SERVER_URL)
        api_key = os.getenv("SECURITY_API_KEY", cls.DEFAULT_API_KEY)
        
        return {
            "server_url": server_url,
            "api_key": api_key,
        }
    
    @classmethod
    def save(cls, server_url: str, api_key: str):
        """
        Save configuration to .env file.
        
        Args:
            server_url: Server URL (e.g., http://192.168.1.100:5000)
            api_key: API key for authentication
        """
        cls.init()
        
        # Set environment variables
        os.environ["SECURITY_SERVER_URL"] = server_url
        os.environ["SECURITY_API_KEY"] = api_key
        
        # Write to .env file
        set_key(str(cls.ENV_FILE), "SECURITY_SERVER_URL", server_url)
        set_key(str(cls.ENV_FILE), "SECURITY_API_KEY", api_key)
    
    @classmethod
    def get_server_url(cls) -> str:
        """Get the configured server URL."""
        config = cls.load()
        return config["server_url"]
    
    @classmethod
    def get_api_key(cls) -> str:
        """Get the configured API key."""
        config = cls.load()
        return config["api_key"]
    
    @classmethod
    def is_configured(cls) -> bool:
        """Check if configuration has valid server URL and API key."""
        config = cls.load()
        return bool(config["server_url"] and config["api_key"])
