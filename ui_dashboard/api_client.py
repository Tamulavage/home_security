"""
API Client for communicating with pi_server REST endpoints.
Handles authentication, error handling, and data parsing.
"""

import time
from typing import Optional, Dict, Any, Iterator
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class ConnectionError(Exception):
    """Raised when unable to connect to the server."""
    pass


class AuthenticationError(Exception):
    """Raised when API key is invalid."""
    pass


class CameraDisabledError(Exception):
    """Raised when camera is disabled on the server."""
    pass


class SecurityAppClient:
    """Client for interacting with pi_server security API."""
    
    def __init__(self, server_url: str, api_key: str, timeout: float = 5.0):
        """
        Initialize the API client.
        
        Args:
            server_url: Base URL of pi_server (e.g., 'http://192.168.1.100:5000')
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session = self._create_session()
        self._camera_enabled = True
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        # Retry strategy: exponential backoff on connection errors
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[503, 502, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API key."""
        return {"X-API-KEY": self.api_key}
    
    def validate_connection(self) -> bool:
        """
        Validate that the server is reachable and API key is valid.
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.server_url}/health",
                timeout=self.timeout
            )
            if response.status_code == 200:
                # Try an authenticated endpoint to verify API key
                response = self.session.get(
                    f"{self.server_url}/status",
                    headers=self._get_headers(),
                    timeout=self.timeout
                )
                return response.status_code == 200
            return False
        except requests.RequestException:
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current system status including temperature, humidity, motion, and camera state.
        
        Returns:
            Dict with keys: temperature_c, humidity, motion_detected, motion_last_seen, camera_enabled
            
        Raises:
            ConnectionError: If unable to connect to server
            AuthenticationError: If API key is invalid
        """
        try:
            response = self.session.get(
                f"{self.server_url}/status",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code != 200:
                raise ConnectionError(f"Server returned status {response.status_code}")
            
            data = response.json()
            # Update camera_enabled flag
            self._camera_enabled = data.get("camera_enabled", True)
            return data
            
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to connect to server: {e}")
    
    def get_motion(self) -> Dict[str, Any]:
        """
        Get current motion detection status.
        
        Returns:
            Dict with keys: motion_detected, motion_last_seen
        """
        try:
            response = self.session.get(
                f"{self.server_url}/motion",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code != 200:
                raise ConnectionError(f"Server returned status {response.status_code}")
            
            return response.json()
            
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to get motion status: {e}")
    
    def get_temperature_humidity(self) -> Dict[str, Any]:
        """
        Get current temperature and humidity readings.
        
        Returns:
            Dict with keys: temperature_c, humidity, temperature_f
        """
        try:
            response = self.session.get(
                f"{self.server_url}/temperature",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code != 200:
                raise ConnectionError(f"Server returned status {response.status_code}")
            
            return response.json()
            
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to get temperature/humidity: {e}")
    
    def get_video_stream(self) -> Iterator[bytes]:
        """
        Get MJPEG video stream as an iterator of frames.
        
        Yields:
            JPEG frame data
            
        Raises:
            ConnectionError: If unable to connect to server
            AuthenticationError: If API key is invalid
            CameraDisabledError: If camera is disabled on server
        """
        try:
            response = self.session.get(
                f"{self.server_url}/video_feed",
                headers=self._get_headers(),
                stream=True,
                timeout=None  # Video streaming has no timeout
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 503:
                raise CameraDisabledError("Camera is currently disabled on server")
            elif response.status_code != 200:
                raise ConnectionError(f"Server returned status {response.status_code}")
            
            # Parse MJPEG stream with boundary separators
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk
                    
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to get video stream: {e}")
    
    def start_camera(self) -> Dict[str, Any]:
        """
        Enable camera on the server.
        
        Returns:
            Dict with status message
            
        Raises:
            ConnectionError: If unable to connect to server
            AuthenticationError: If API key is invalid
        """
        try:
            response = self.session.post(
                f"{self.server_url}/camera/start",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code != 200:
                raise ConnectionError(f"Server returned status {response.status_code}")
            
            self._camera_enabled = True
            return response.json()
            
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to start camera: {e}")
    
    def stop_camera(self) -> Dict[str, Any]:
        """
        Disable camera on the server.
        
        Returns:
            Dict with status message
            
        Raises:
            ConnectionError: If unable to connect to server
            AuthenticationError: If API key is invalid
        """
        try:
            response = self.session.post(
                f"{self.server_url}/camera/stop",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code != 200:
                raise ConnectionError(f"Server returned status {response.status_code}")
            
            self._camera_enabled = False
            return response.json()
            
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to stop camera: {e}")
    
    @property
    def camera_enabled(self) -> bool:
        """Get the last known camera enabled state."""
        return self._camera_enabled
