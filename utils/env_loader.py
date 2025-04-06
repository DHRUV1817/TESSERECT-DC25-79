"""
Environment Configuration Loader for the Tesseract Project
Loads environment variables from .env file.
"""
import os
import logging
from typing import Dict, Any, Optional

# Try to import dotenv, but make it optional
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

class EnvConfig:
    """Handles environment configuration loading."""
    
    def __init__(self, env_file: str = ".env"):
        """
        Initialize the environment configuration loader.
        
        Args:
            env_file: Path to the .env file
        """
        # Load environment variables from .env file if available
        if DOTENV_AVAILABLE:
            load_dotenv(dotenv_path=env_file)
        
        # Load API configuration
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8000"))
        self.api_reload = self._parse_bool(os.getenv("API_RELOAD", "true"))
        
        # Load UI configuration
        self.ui_port = int(os.getenv("UI_PORT", "8501"))
        self.browser_auto_open = self._parse_bool(os.getenv("BROWSER_AUTO_OPEN", "true"))
        
        # Load logging configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_dir = os.getenv("LOG_DIR", "logs")
        
        # Create log directory if it doesn't exist
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)
    
    def _parse_bool(self, value: Optional[str]) -> bool:
        """Parse a string value as a boolean."""
        if value is None:
            return False
            
        return value.lower() in ("yes", "true", "t", "1", "on")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary of configuration values
        """
        return {
            "api_host": self.api_host,
            "api_port": self.api_port,
            "api_reload": self.api_reload,
            "ui_port": self.ui_port,
            "browser_auto_open": self.browser_auto_open,
            "log_level": self.log_level,
            "log_dir": self.log_dir
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value or default
        """
        return getattr(self, key, default)

# Singleton instance
_config_instance = None

def get_config(env_file: str = ".env") -> EnvConfig:
    """
    Get the configuration instance.
    
    Args:
        env_file: Path to .env file
        
    Returns:
        EnvConfig instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = EnvConfig(env_file)
    return _config_instance