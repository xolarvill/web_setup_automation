from app import WSA
from PySide6.QtWidgets import QApplication
import sys

def main():
    app = QApplication(sys.argv)
    window = WSA()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()