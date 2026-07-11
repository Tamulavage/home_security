"""
Main window for the security dashboard application.
"""

import threading
import time
import io
from datetime import datetime
from typing import Optional
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QDialog, QLabel, QGroupBox, QMessageBox, QStatusBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont

from config import Config
from api_client import (
    SecurityAppClient, ConnectionError, AuthenticationError, CameraDisabledError
)

from .widgets import (
    VideoStreamWidget, MotionIndicatorWidget, TemperatureHumidityWidget,
    StatusLabel, CameraControlButton, SettingsPanel
)
from .styles import MAIN_STYLESHEET


class APIWorker(QObject):
    """Worker thread for API calls without blocking UI."""
    
    status_updated = pyqtSignal(dict)
    video_frame = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)
    connected = pyqtSignal(bool)
    
    def __init__(self, client: SecurityAppClient):
        super().__init__()
        self.client = client
        self.running = True
        self.video_streaming = False
    
    def poll_status(self):
        """Poll server status in a background thread."""
        while self.running:
            try:
                status = self.client.get_status()
                self.status_updated.emit(status)
                self.connected.emit(True)
            except (ConnectionError, AuthenticationError) as e:
                self.error_occurred.emit(str(e))
                self.connected.emit(False)
            except Exception as e:
                self.error_occurred.emit(f"Unexpected error: {str(e)}")
                self.connected.emit(False)
            
            time.sleep(2)  # Poll every 2 seconds
    
    def stream_video(self):
        """Stream video from server."""
        self.video_streaming = True
        frame_buffer = b""
        
        try:
            for chunk in self.client.get_video_stream():
                if not self.video_streaming or not self.running:
                    break
                
                frame_buffer += chunk
                
                # Look for JPEG frame boundaries
                if b"\xff\xd8" in frame_buffer and b"\xff\xd9" in frame_buffer:
                    start = frame_buffer.find(b"\xff\xd8")
                    end = frame_buffer.find(b"\xff\xd9", start) + 2
                    
                    if start != -1 and end > start:
                        frame_data = frame_buffer[start:end]
                        self.video_frame.emit(frame_data)
                        frame_buffer = frame_buffer[end:]
        
        except CameraDisabledError:
            self.error_occurred.emit("Camera is disabled on server")
            self.video_streaming = False
        except (ConnectionError, AuthenticationError) as e:
            self.error_occurred.emit(str(e))
            self.video_streaming = False
        except Exception as e:
            if self.video_streaming:  # Only report if we weren't trying to stop
                self.error_occurred.emit(f"Video stream error: {str(e)}")
            self.video_streaming = False
    
    def stop(self):
        """Stop all operations."""
        self.running = False
        self.video_streaming = False


class MainWindow(QMainWindow):
    """Main dashboard window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Security Dashboard")
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet(MAIN_STYLESHEET)
        
        # API client
        self.client: Optional[SecurityAppClient] = None
        self.worker: Optional[APIWorker] = None
        self.status_thread: Optional[threading.Thread] = None
        self.video_thread: Optional[threading.Thread] = None
        
        # UI components
        self._init_ui()
        
        # Timer for periodic updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._on_timer_tick)
        self.update_timer.start(1000)  # 1 second timer for time display
        
        # Initialize or prompt for configuration
        self._init_client()
    
    def _init_ui(self):
        """Initialize UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Video display
        self.video_widget = VideoStreamWidget()
        main_layout.addWidget(self.video_widget)
        
        # Camera control buttons
        button_layout = QHBoxLayout()
        
        self.camera_button = CameraControlButton()
        self.camera_button.clicked.connect(self._on_camera_button_clicked)
        button_layout.addWidget(self.camera_button)
        
        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self._on_settings_clicked)
        button_layout.addWidget(settings_button)
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self._on_refresh_clicked)
        button_layout.addWidget(refresh_button)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # Status group
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        self.status_label = StatusLabel()
        status_layout.addWidget(self.status_label)
        
        self.motion_indicator = MotionIndicatorWidget()
        status_layout.addWidget(self.motion_indicator)
        
        self.temp_humidity = TemperatureHumidityWidget()
        status_layout.addWidget(self.temp_humidity)
        
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        central_widget.setLayout(main_layout)
        
        # Status bar
        self.statusBar().showMessage("Initializing...")
    
    def _init_client(self):
        """Initialize API client or prompt for configuration."""
        config = Config.load()
        server_url = config.get("server_url", "")
        api_key = config.get("api_key", "")
        
        if server_url and api_key:
            self._create_client(server_url, api_key)
        else:
            self._show_settings_dialog()
    
    def _create_client(self, server_url: str, api_key: str):
        """Create API client and start background threads."""
        try:
            # Validate connection first
            test_client = SecurityAppClient(server_url, api_key)
            if not test_client.validate_connection():
                QMessageBox.warning(
                    self, "Connection Failed",
                    "Unable to connect to server. Please check the server URL and API key."
                )
                self._show_settings_dialog()
                return
            
            # Create actual client
            self.client = SecurityAppClient(server_url, api_key)
            
            # Save configuration
            Config.save(server_url, api_key)
            
            # Create worker
            self.worker = APIWorker(self.client)
            self.worker.status_updated.connect(self._on_status_updated)
            self.worker.video_frame.connect(self._on_video_frame)
            self.worker.error_occurred.connect(self._on_error)
            self.worker.connected.connect(self._on_connected)
            
            # Start status polling thread
            self.status_thread = threading.Thread(
                target=self.worker.poll_status,
                daemon=True
            )
            self.status_thread.start()
            
            # Start video streaming
            self.video_thread = threading.Thread(
                target=self.worker.stream_video,
                daemon=True
            )
            self.video_thread.start()
            
            self.status_label.set_status("connecting")
            self.statusBar().showMessage("Connected to server")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize client: {str(e)}")
            self._show_settings_dialog()
    
    def _show_settings_dialog(self):
        """Show settings dialog for configuration."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Server Configuration")
        dialog.setGeometry(200, 200, 400, 200)
        
        layout = QVBoxLayout()
        
        # Settings panel
        self.settings_panel = SettingsPanel()
        
        # Load existing settings
        config = Config.load()
        self.settings_panel.set_server_url(config.get("server_url", ""))
        self.settings_panel.set_api_key(config.get("api_key", ""))
        
        layout.addWidget(self.settings_panel)
        
        # Save button
        save_button = QPushButton("Connect & Save")
        save_button.clicked.connect(
            lambda: self._on_settings_save(dialog)
        )
        layout.addWidget(save_button)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def _on_settings_clicked(self):
        """Handle settings button click."""
        self._show_settings_dialog()
    
    def _on_settings_save(self, dialog: QDialog):
        """Handle settings save."""
        server_url = self.settings_panel.get_server_url().strip()
        api_key = self.settings_panel.get_api_key().strip()
        
        if not server_url or not api_key:
            QMessageBox.warning(self, "Validation Error", "Server URL and API Key are required")
            return
        
        # Stop existing threads
        if self.worker:
            self.worker.stop()
        
        # Create new client with new settings
        self._create_client(server_url, api_key)
        dialog.close()
    
    def _on_camera_button_clicked(self):
        """Handle camera button click."""
        if not self.client:
            QMessageBox.warning(self, "Error", "Not connected to server")
            return
        
        self.camera_button.set_loading(True)
        
        def toggle_camera():
            try:
                if self.client.camera_enabled:
                    self.client.stop_camera()
                else:
                    self.client.start_camera()
                    self.worker.video_streaming = True
                    if not self.video_thread.is_alive():
                        self.video_thread = threading.Thread(
                            target=self.worker.stream_video,
                            daemon=True
                        )
                        self.video_thread.start()

                # Refresh status
                status = self.client.get_status()
                self.status_updated_emit = pyqtSignal(dict)
                self._on_status_updated(status)
            except Exception as e:
                self._on_error(f"Camera control error: {str(e)}")
            finally:
                self.camera_button.set_loading(False)
        
        thread = threading.Thread(target=toggle_camera, daemon=True)
        thread.start()
    
    def _on_refresh_clicked(self):
        """Handle refresh button click."""
        if not self.client:
            return
        
        def refresh():
            try:
                status = self.client.get_status()
                self._on_status_updated(status)
            except Exception as e:
                self._on_error(str(e))
        
        thread = threading.Thread(target=refresh, daemon=True)
        thread.start()
    
    def _on_status_updated(self, status: dict):
        """Handle status update from worker."""
        self.motion_indicator.set_motion_detected(status.get("motion_detected", False))
        self.temp_humidity.update_data(
            status.get("temperature_f"),
            status.get("humidity")
        )
        self.camera_button.set_camera_state(status.get("camera_enabled", True))
    
    def _on_video_frame(self, frame_data: bytes):
        """Handle video frame from worker."""
        self.video_widget.display_frame(frame_data)
    
    def _on_error(self, error_msg: str):
        """Handle error from worker."""
        self.statusBar().showMessage(f"Error: {error_msg}")
    
    def _on_connected(self, connected: bool):
        """Handle connection status change."""
        if connected:
            self.status_label.set_status("connected")
            self.motion_indicator.set_connected(True)
        else:
            self.status_label.set_status("disconnected")
            self.motion_indicator.set_connected(False)
            self.video_widget.clear_video()
    
    def _on_timer_tick(self):
        """Handle periodic timer tick."""
        now = datetime.now().strftime("%H:%M:%S")
        self.status_label.set_update_time(now)
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.worker:
            self.worker.stop()
        
        # Wait for threads to finish
        if self.status_thread:
            self.status_thread.join(timeout=2)
        if self.video_thread:
            self.video_thread.join(timeout=2)
        
        event.accept()
