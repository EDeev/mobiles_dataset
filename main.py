import sys
import logging
from PyQt6.QtWidgets import QApplication

from main_window import MainWindow

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    app = QApplication(sys.argv)
    
    # Настройки приложения
    app.setApplicationName("Mobile Devices Manager")
    app.setOrganizationName("Moscow Polytech")
    
    # Устанавливаем стиль
    app.setStyle('Fusion')
    
    # Создаем и показываем главное окно
    window = MainWindow()
    window.show()
    
    # Запускаем цикл обработки событий
    sys.exit(app.exec())

if __name__ == "__main__":
    main()