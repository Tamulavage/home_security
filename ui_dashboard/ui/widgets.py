"""
Reusable PyQt5 widgets for the security dashboard.
"""

import io
from typing import Optional, Callable
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QScrollArea, QFrame
)
from PyQt5.QtGui import QPixmap, QFont, QColor, QImage
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PIL import Image

from .styles import (
    MOTION_DETECTED_COLOR, MOTION_CLEAR_COLOR, MOTION_UNKNOWN_COLOR,
    get_motion_indicator_style, STATUS_CONNECTED_COLOR, STATUS_DISCONNECTED_COLOR
)


class VideoStreamWidget(QLabel):
    """Display MJPEG video stream from the server."""
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: black; border: 2px solid #333;")
        self.setScaledContents(False)
        self.setText("No Video")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(640, 480)
    
    def display_frame(self, frame_data: bytes):
        """Display a single frame from JPEG data."""
        try:
            image = Image.open(io.BytesIO(frame_data))
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize to fit widget while maintaining aspect ratio
            image.thumbnail((640, 480), Image.Resampling.LANCZOS)
            
            # Convert to QPixmap
            data = image.tobytes("raw", "RGB")
            qimg = QImage(data, image.width, image.height, 3 * image.width, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            
            self.setPixmap(pixmap)
        except Exception as e:
            self.setText(f"Error loading frame: {str(e)}")
    
    def clear_video(self):
        """Clear the video display."""
        self.clear()
        self.setText("Video Stopped")


class MotionIndicatorWidget(QWidget):
    """Display motion detection status with visual indicator."""
    
    def __init__(self):
        super().__init__()
        self.motion_detected = False
        self.connected = False
        self._init_ui()
    
    def _init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Indicator circle
        self.indicator = QLabel()
        self.indicator.setFixedSize(20, 20)
        self.indicator.setStyleSheet(f"""
            background-color: {MOTION_CLEAR_COLOR};
            border-radius: 10px;
            border: 2px solid #333;
        """)
        
        # Status text
        self.status_label = QLabel("No Motion")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        layout.addWidget(self.indicator)
        layout.addWidget(self.status_label)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def set_motion_detected(self, detected: bool):
        """Update motion detection status."""
        self.motion_detected = detected
        self._update_display()
    
    def set_connected(self, connected: bool):
        """Update connection status."""
        self.connected = connected
        self._update_display()
    
    def _update_display(self):
        """Update the visual display based on current state."""
        if not self.connected:
            color = "#999999"
            text = "Disconnected"
        elif self.motion_detected:
            color = MOTION_DETECTED_COLOR
            text = "Motion Detected!"
        else:
            color = MOTION_CLEAR_COLOR
            text = "No Motion"
        
        self.indicator.setStyleSheet(f"""
            background-color: {color};
            border-radius: 10px;
            border: 2px solid #333;
        """)
        self.status_label.setText(text)


class TemperatureHumidityWidget(QWidget):
    """Display temperature and humidity readings."""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Temperature
        self.temp_label = QLabel("Temp: --°F")
        self.temp_label.setFont(QFont("Arial", 12))
        
        # Humidity
        self.humidity_label = QLabel("Humidity: --%")
        self.humidity_label.setFont(QFont("Arial", 12))
        
        layout.addWidget(self.temp_label)
        layout.addSpacing(20)
        layout.addWidget(self.humidity_label)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def update_data(self, temperature: Optional[float], humidity: Optional[float]):
        """Update temperature and humidity display."""
        temp_text = f"Temp: {temperature:.2f}°F" if temperature is not None else "Temp: --°F"
        humidity_text = f"Humidity: {humidity:.1f}%" if humidity is not None else "Humidity: --%"
        
        self.temp_label.setText(temp_text)
        self.humidity_label.setText(humidity_text)


class StatusLabel(QWidget):
    """Display connection status and last update time."""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Arial", 16))
        self.status_indicator.setFixedWidth(20)
        
        # Status text
        self.status_text = QLabel("Disconnected")
        self.status_text.setFont(QFont("Arial", 11))
        
        # Last update time
        self.update_time = QLabel("")
        self.update_time.setFont(QFont("Arial", 10))
        self.update_time.setStyleSheet("color: #666666;")
        
        layout.addWidget(self.status_indicator)
        layout.addWidget(self.status_text)
        layout.addSpacing(20)
        layout.addWidget(self.update_time)
        layout.addStretch()
        
        self.setLayout(layout)
        self.set_status("disconnected")
    
    def set_status(self, status: str):
        """
        Set the connection status.
        
        Args:
            status: One of 'connected', 'disconnected', 'connecting'
        """
        color_map = {
            "connected": STATUS_CONNECTED_COLOR,
            "disconnected": STATUS_DISCONNECTED_COLOR,
            "connecting": "#ffaa00",
        }
        text_map = {
            "connected": "Connected",
            "disconnected": "Disconnected",
            "connecting": "Connecting...",
        }
        
        color = color_map.get(status, STATUS_DISCONNECTED_COLOR)
        text = text_map.get(status, "Unknown")
        
        self.status_indicator.setStyleSheet(f"color: {color};")
        self.status_text.setText(text)
    
    def set_update_time(self, time_str: str):
        """Set the last update time display."""
        self.update_time.setText(f"Last update: {time_str}")


class CameraControlButton(QPushButton):
    """Button for controlling camera on/off with loading state."""
    
    state_changed = pyqtSignal(bool)  # True for enabled, False for disabled
    
    def __init__(self):
        super().__init__()
        self.is_camera_enabled = True
        self._update_display()
        self.clicked.connect(self._on_click)
    
    def _update_display(self):
        """Update button appearance based on camera state."""
        if self.is_camera_enabled:
            self.setText("Stop Camera")
            self.setObjectName("dangerButton")
        else:
            self.setText("Start Camera")
            self.setObjectName("successButton")
    
    def set_camera_state(self, enabled: bool):
        """Set the camera state and update display."""
        self.is_camera_enabled = enabled
        self._update_display()
    
    def set_loading(self, loading: bool):
        """Show/hide loading state."""
        if loading:
            self.setText("...")
            self.setEnabled(False)
        else:
            self._update_display()
            self.setEnabled(True)
    
    def _on_click(self):
        """Handle button click."""
        self.state_changed.emit(not self.is_camera_enabled)


class LoadingSpinner(QWidget):
    """Simple spinning loading indicator."""
    
    def __init__(self):
        super().__init__()
        self.label = QLabel("⏳ Loading...")
        self.label.setFont(QFont("Arial", 11))
        layout = QHBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
    
    def show_message(self, message: str):
        """Display a loading message."""
        self.label.setText(f"⏳ {message}")
    
    def hide_loading(self):
        """Hide the loading indicator."""
        self.label.setText("")


class SettingsPanel(QWidget):
    """Settings panel for configuring server connection."""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        from PyQt5.QtWidgets import QLineEdit, QLabel, QFormLayout
        
        layout = QFormLayout()
        
        # Server URL input
        self.server_url_input = QLineEdit()
        self.server_url_input.setPlaceholderText("http://192.168.1.100:5000")
        layout.addRow("Server URL:", self.server_url_input)
        
        # API Key input
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your API key")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        layout.addRow("API Key:", self.api_key_input)
        
        # Test button
        self.test_button = QPushButton("Test Connection")
        layout.addRow("", self.test_button)
        
        self.setLayout(layout)
    
    def get_server_url(self) -> str:
        """Get the entered server URL."""
        return self.server_url_input.text()
    
    def get_api_key(self) -> str:
        """Get the entered API key."""
        return self.api_key_input.text()
    
    def set_server_url(self, url: str):
        """Set the server URL input."""
        self.server_url_input.setText(url)
    
    def set_api_key(self, key: str):
        """Set the API key input."""
        self.api_key_input.setText(key)
