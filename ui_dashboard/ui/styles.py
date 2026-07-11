"""
PyQt5 stylesheet and styling utilities for the security dashboard.
"""

MAIN_STYLESHEET = """
QMainWindow {
    background-color: #f0f0f0;
}

QWidget {
    background-color: #f0f0f0;
    color: #333333;
}

QLabel {
    color: #333333;
}

QPushButton {
    background-color: #0078d4;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #0063b1;
}

QPushButton:pressed {
    background-color: #005299;
}

QPushButton:disabled {
    background-color: #cccccc;
    color: #666666;
}

QPushButton#dangerButton {
    background-color: #d32f2f;
}

QPushButton#dangerButton:hover {
    background-color: #b71c1c;
}

QPushButton#successButton {
    background-color: #388e3c;
}

QPushButton#successButton:hover {
    background-color: #2e7d32;
}

QGroupBox {
    color: #333333;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px 0 3px;
}

QLineEdit, QSpinBox {
    background-color: white;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 6px;
    color: #333333;
}

QLineEdit:focus, QSpinBox:focus {
    border: 2px solid #0078d4;
}

QDialog {
    background-color: #f0f0f0;
}

QHeaderView::section {
    background-color: #e0e0e0;
    padding: 5px;
    border: 1px solid #d0d0d0;
}
"""

# Motion indicator colors
MOTION_DETECTED_COLOR = "#ff0000"  # Red
MOTION_CLEAR_COLOR = "#00aa00"      # Green
MOTION_UNKNOWN_COLOR = "#cccccc"    # Gray

# Status indicator colors
STATUS_CONNECTED_COLOR = "#00aa00"  # Green
STATUS_DISCONNECTED_COLOR = "#ff0000"  # Red
STATUS_CONNECTING_COLOR = "#ffaa00"  # Orange

# Fonts
TITLE_FONT_SIZE = 14
NORMAL_FONT_SIZE = 12
SMALL_FONT_SIZE = 10


def get_motion_indicator_style(motion_detected: bool, connected: bool) -> str:
    """Get stylesheet for motion indicator based on state."""
    if not connected:
        color = STATUS_DISCONNECTED_COLOR
        tooltip = "Disconnected"
    elif motion_detected:
        color = MOTION_DETECTED_COLOR
        tooltip = "Motion Detected!"
    else:
        color = MOTION_CLEAR_COLOR
        tooltip = "No Motion"
    
    return f"""
    QWidget {{
        border: 2px solid {color};
        border-radius: 8px;
        background-color: white;
    }}
    """


def get_status_indicator_style(status: str) -> str:
    """Get stylesheet for status indicator based on connection status."""
    color_map = {
        "connected": STATUS_CONNECTED_COLOR,
        "disconnected": STATUS_DISCONNECTED_COLOR,
        "connecting": STATUS_CONNECTING_COLOR,
    }
    color = color_map.get(status, STATUS_DISCONNECTED_COLOR)
    
    return f"""
    background-color: {color};
    border-radius: 6px;
    """
