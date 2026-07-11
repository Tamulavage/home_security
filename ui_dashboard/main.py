"""
Security Dashboard Application Entry Point

Run with: python -m ui_dashboard.main
Or: python main.py (from ui_dashboard directory)
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from ui.main_window import MainWindow


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' 
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the application."""
    try:
        app = QApplication(sys.argv)
        
        # Set application properties
        app.setApplicationName("Security Dashboard")
        app.setApplicationVersion("1.0.0")
        app.setStyle('Fusion')
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Run application
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.critical(f"Failed to start application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
