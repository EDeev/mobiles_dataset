# ui/main_window.py
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QTabWidget,
    QLabel, QLineEdit, QComboBox, QSpinBox, QMessageBox,
    QDialog, QFormLayout, QDialogButtonBox, QHeaderView,
    QToolBar, QStatusBar, QGroupBox, QTextEdit, QInputDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QFont
from typing import Dict, Any
import logging

# Импортируем наш модуль БД
from database import Database

logger = logging.getLogger(__name__)

# Маппинг валют по регионам
CURRENCY_MAP = {
    'Pakistan': ('PKR', '₨'),
    'India': ('INR', '₹'),
    'China': ('CNY', '¥'),
    'USA': ('USD', '$'),
    'Dubai': ('AED', 'د.إ')
}

class ModelDialog(QDialog):
    """Диалог для добавления/редактирования модели"""
    
    def __init__(self, parent=None, model_data=None):
        super().__init__(parent)
        self.model_data = model_data
        self.db = Database()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Добавить модель" if not self.model_data else "Редактировать модель")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QFormLayout()
        
        # Поля формы
        self.company_combo = QComboBox()
        companies = self.db.get_all_companies()
        for company in companies:
            self.company_combo.addItem(company['company_name'], company['company_id'])
        
        self.model_name_edit = QLineEdit()
        self.weight_edit = QLineEdit()
        self.ram_edit = QLineEdit()
        self.front_camera_edit = QLineEdit()
        self.back_camera_edit = QLineEdit()
        self.processor_edit = QLineEdit()
        self.battery_edit = QLineEdit()
        self.screen_edit = QLineEdit()
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2030)
        self.year_spin.setValue(2024)
        
        # Добавляем поля в форму
        layout.addRow("Компания:", self.company_combo)
        layout.addRow("Название модели:", self.model_name_edit)
        layout.addRow("Вес:", self.weight_edit)
        layout.addRow("RAM:", self.ram_edit)
        layout.addRow("Фронтальная камера:", self.front_camera_edit)
        layout.addRow("Основная камера:", self.back_camera_edit)
        layout.addRow("Процессор:", self.processor_edit)
        layout.addRow("Батарея:", self.battery_edit)
        layout.addRow("Размер экрана:", self.screen_edit)
        layout.addRow("Год выпуска:", self.year_spin)
        
        # Заполняем данные при редактировании
        if self.model_data:
            self.model_name_edit.setText(self.model_data.get('model_name', ''))
            self.weight_edit.setText(self.model_data.get('mobile_weight', ''))
            self.ram_edit.setText(self.model_data.get('ram', ''))
            self.front_camera_edit.setText(self.model_data.get('front_camera', ''))
            self.back_camera_edit.setText(self.model_data.get('back_camera', ''))
            self.processor_edit.setText(self.model_data.get('processor_name', ''))
            self.battery_edit.setText(self.model_data.get('battery_capacity', ''))
            self.screen_edit.setText(self.model_data.get('screen_size', ''))
            if self.model_data.get('launched_year'):
                self.year_spin.setValue(self.model_data['launched_year'])
            
            # Устанавливаем компанию
            for i in range(self.company_combo.count()):
                if self.company_combo.itemData(i) == self.model_data.get('company_id'):
                    self.company_combo.setCurrentIndex(i)
                    break
        
        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addRow(buttons)
        self.setLayout(layout)
    
    def get_data(self) -> Dict[str, Any]:
        """Получение данных из формы"""
        return {
            'company_id': self.company_combo.currentData(),
            'model_name': self.model_name_edit.text(),
            'mobile_weight': self.weight_edit.text() or None,
            'ram': self.ram_edit.text() or None,
            'front_camera': self.front_camera_edit.text() or None,
            'back_camera': self.back_camera_edit.text() or None,
            'processor_name': self.processor_edit.text() or None,
            'battery_capacity': self.battery_edit.text() or None,
            'screen_size': self.screen_edit.text() or None,
            'launched_year': self.year_spin.value()
        }


class PriceDialog(QDialog):
    """Диалог для управления ценами модели"""
    
    def __init__(self, parent=None, model_id=None, model_name=""):
        super().__init__(parent)
        self.model_id = model_id
        self.model_name = model_name
        self.db = Database()
        self.init_ui()
        self.load_prices()
        
    def init_ui(self):
        self.setWindowTitle(f"Цены для: {self.model_name}")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # Таблица цен
        self.prices_table = QTableWidget()
        self.prices_table.setColumnCount(4)
        self.prices_table.setHorizontalHeaderLabels(["Регион", "Цена", "Валюта", "Действия"])
        self.prices_table.setSortingEnabled(True)
        
        # Настройка размеров столбцов
        header = self.prices_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.prices_table)
        
        # Форма добавления цены
        add_group = QGroupBox("Добавить/Обновить цену")
        add_layout = QHBoxLayout()
        
        self.region_combo = QComboBox()
        regions = self.db.get_all_regions()
        for region in regions:
            self.region_combo.addItem(region['region_name'], region['region_id'])
        
        self.price_edit = QLineEdit()
        self.price_edit.setPlaceholderText("Цена")
        
        add_btn = QPushButton("Добавить/Обновить")
        add_btn.clicked.connect(self.add_update_price)
        
        add_layout.addWidget(QLabel("Регион:"))
        add_layout.addWidget(self.region_combo)
        add_layout.addWidget(QLabel("Цена:"))
        add_layout.addWidget(self.price_edit)
        add_layout.addWidget(add_btn)
        
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def format_price(self, price: float, region_name: str) -> str:
        """Форматирование цены с правильным символом валюты"""
        currency_code, currency_symbol = CURRENCY_MAP.get(region_name, ('USD', '$'))
        return f"{currency_symbol}{price:,.2f}"
    
    def load_prices(self):
        """Загрузка цен из БД"""
        prices = self.db.get_model_prices(self.model_id)
        self.prices_table.setRowCount(len(prices))
        
        for row, price_data in enumerate(prices):
            # Регион
            region_item = QTableWidgetItem(price_data['region_name'])
            region_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.prices_table.setItem(row, 0, region_item)
            
            # Цена с правильной валютой
            price_str = self.format_price(price_data['price'], price_data['region_name'])
            price_item = QTableWidgetItem(price_str)
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.prices_table.setItem(row, 1, price_item)
            
            # Код валюты
            currency_code, _ = CURRENCY_MAP.get(price_data['region_name'], ('USD', '$'))
            currency_item = QTableWidgetItem(currency_code)
            currency_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.prices_table.setItem(row, 2, currency_item)
            
            # Кнопка удаления
            delete_btn = QPushButton("Удалить")
            delete_btn.clicked.connect(lambda checked, pid=price_data['price_id']: self.delete_price(pid))
            self.prices_table.setCellWidget(row, 3, delete_btn)
    
    def add_update_price(self):
        """Добавление или обновление цены"""
        try:
            region_id = self.region_combo.currentData()
            price = float(self.price_edit.text())
            
            self.db.add_or_update_price(self.model_id, region_id, price)
            self.load_prices()
            self.price_edit.clear()
            
            QMessageBox.information(self, "Успех", "Цена успешно обновлена!")
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректную цену!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении цены: {str(e)}")
    
    def delete_price(self, price_id):
        """Удаление цены"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Вы уверены, что хотите удалить эту цену?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_price(price_id)
                self.load_prices()
                QMessageBox.information(self, "Успех", "Цена удалена!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.init_ui()
        self.connect_to_db()
        
    def init_ui(self):
        self.setWindowTitle("Датасет мобильных устройств")
        self.setGeometry(100, 100, 1200, 600)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        layout = QVBoxLayout(central_widget)
        
        # Создаем панель инструментов
        self.create_toolbar()
        
        # Создаем вкладки
        self.tabs = QTabWidget()
        
        # Вкладка компаний
        self.companies_tab = self.create_companies_tab()
        self.tabs.addTab(self.companies_tab, "🏢 Компании")
        
        # Вкладка моделей
        self.models_tab = self.create_models_tab()
        self.tabs.addTab(self.models_tab, "📱 Модели")
        
        # Вкладка аналитики
        self.analytics_tab = self.create_analytics_tab()
        self.tabs.addTab(self.analytics_tab, "📊 Аналитика")
        
        layout.addWidget(self.tabs)
        
        # Статусная строка
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")
        
    def create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Действия
        refresh_action = QAction("🔄 Обновить", self)
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        add_company_action = QAction("➕ Добавить компанию", self)
        add_company_action.triggered.connect(self.add_company)
        toolbar.addAction(add_company_action)
        
        toolbar.addSeparator()
        
        add_model_action = QAction("➕ Добавить модель", self)
        add_model_action.triggered.connect(self.add_model)
        toolbar.addAction(add_model_action)
        
    def create_companies_tab(self) -> QWidget:
        """Создание вкладки компаний"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Панель управления
        control_panel = QHBoxLayout()
        control_panel.addStretch()
        layout.addLayout(control_panel)
        
        # Таблица компаний
        self.companies_table = QTableWidget()
        self.companies_table.setColumnCount(3)
        self.companies_table.setHorizontalHeaderLabels(["ID", "Название компании", "Кол-во моделей"])
        self.companies_table.setSortingEnabled(True)
        
        # Настройка размеров столбцов
        header = self.companies_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.companies_table)
        
        return widget
    
    def create_models_tab(self) -> QWidget:
        """Создание вкладки моделей"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Панель поиска
        search_panel = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Поиск по названию, компании, RAM...")
        self.search_edit.textChanged.connect(self.search_models)
        search_panel.addWidget(self.search_edit)
        
        layout.addLayout(search_panel)
        
        # Таблица моделей
        self.models_table = QTableWidget()
        self.models_table.setColumnCount(11)
        self.models_table.setHorizontalHeaderLabels([
            "ID", "Компания", "Модель", "RAM", "Батарея", 
            "Экран", "Год", "Регионов с ценами", "Действия", "", ""
        ])
        self.models_table.setSortingEnabled(True)
        
        # Настройка размеров столбцов
        header = self.models_table.horizontalHeader()
        # ID - минимальный размер
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        # Компания и Модель - расширяемые
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        # Характеристики - по содержимому
        for i in range(3, 8):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        # Кнопки действий - фиксированные
        for i in range(8, 11):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(i, 120)
        
        layout.addWidget(self.models_table)
        
        return widget
    
    def create_analytics_tab(self) -> QWidget:
        """Создание вкладки аналитики"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Статистика по регионам
        stats_group = QGroupBox("📊 Статистика цен по регионам")
        stats_layout = QVBoxLayout()
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setFont(QFont("Consolas", 10))
        stats_layout.addWidget(self.stats_text)
        
        refresh_stats_btn = QPushButton("🔄 Обновить статистику")
        refresh_stats_btn.clicked.connect(self.update_statistics)
        stats_layout.addWidget(refresh_stats_btn)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        return widget
    
    def connect_to_db(self):
        """Подключение к БД"""
        if self.db.connect():
            self.status_bar.showMessage("✅ Подключено к БД")
            self.refresh_data()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к БД!")
    
    def refresh_data(self):
        """Обновление всех данных"""
        self.load_companies()
        self.load_models()
        self.update_statistics()
        self.status_bar.showMessage("✅ Данные обновлены")
    
    def load_companies(self):
        """Загрузка списка компаний"""
        companies = self.db.get_all_companies()
        self.companies_table.setRowCount(len(companies))
        
        for row, company in enumerate(companies):
            # ID
            id_item = QTableWidgetItem(str(company['company_id']))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.companies_table.setItem(row, 0, id_item)
            
            # Название
            name_item = QTableWidgetItem(company['company_name'])
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.companies_table.setItem(row, 1, name_item)
            
            # Количество моделей
            count_item = QTableWidgetItem(str(company['models_count']))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.companies_table.setItem(row, 2, count_item)
    
    def load_models(self, search_text=""):
        """Загрузка списка моделей"""
        if search_text:
            models = self.db.search_models(search_text)
        else:
            models = self.db.get_all_models()
        
        self.models_table.setRowCount(len(models))
        
        for row, model in enumerate(models):
            # ID
            id_item = QTableWidgetItem(str(model['model_id']))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.models_table.setItem(row, 0, id_item)
            
            # Компания
            company_item = QTableWidgetItem(model['company_name'])
            company_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.models_table.setItem(row, 1, company_item)
            
            # Модель
            model_item = QTableWidgetItem(model['model_name'])
            model_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.models_table.setItem(row, 2, model_item)
            
            # RAM
            ram_item = QTableWidgetItem(model.get('ram', ''))
            ram_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.models_table.setItem(row, 3, ram_item)
            
            # Батарея
            battery_item = QTableWidgetItem(model.get('battery_capacity', ''))
            battery_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.models_table.setItem(row, 4, battery_item)
            
            # Экран
            screen_item = QTableWidgetItem(model.get('screen_size', ''))
            screen_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.models_table.setItem(row, 5, screen_item)
            
            # Год
            year_item = QTableWidgetItem(str(model.get('launched_year', '')))
            year_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.models_table.setItem(row, 6, year_item)
            
            # Регионов с ценами
            regions_item = QTableWidgetItem(str(model.get('price_regions', 0)))
            regions_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.models_table.setItem(row, 7, regions_item)
            
            # Кнопки действий
            edit_btn = QPushButton("✏️ Редакт.")
            edit_btn.clicked.connect(lambda checked, mid=model['model_id']: self.edit_model(mid))
            self.models_table.setCellWidget(row, 8, edit_btn)
            
            price_btn = QPushButton("💰 Цены")
            price_btn.clicked.connect(
                lambda checked, mid=model['model_id'], name=model['model_name']: 
                self.manage_prices(mid, name)
            )
            self.models_table.setCellWidget(row, 9, price_btn)
            
            delete_btn = QPushButton("🗑️ Удалить")
            delete_btn.clicked.connect(lambda checked, mid=model['model_id']: self.delete_model(mid))
            self.models_table.setCellWidget(row, 10, delete_btn)
    
    def add_company(self):
        """Добавление новой компании"""
        name, ok = QInputDialog.getText(self, "Новая компания", "Введите название компании:")
        if ok and name:
            try:
                self.db.add_company(name)
                self.refresh_data()
                QMessageBox.information(self, "Успех", f"Компания '{name}' добавлена!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении: {str(e)}")
    
    def add_model(self):
        """Добавление новой модели"""
        dialog = ModelDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                model_data = dialog.get_data()
                self.db.add_model(model_data)
                self.refresh_data()
                QMessageBox.information(self, "Успех", "Модель добавлена!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении: {str(e)}")
    
    def edit_model(self, model_id):
        """Редактирование модели"""
        model_data = self.db.get_model_by_id(model_id)
        dialog = ModelDialog(self, model_data)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                updated_data = dialog.get_data()
                self.db.update_model(model_id, updated_data)
                self.refresh_data()
                QMessageBox.information(self, "Успех", "Модель обновлена!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении: {str(e)}")
    
    def delete_model(self, model_id):
        """Удаление модели"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Вы уверены, что хотите удалить эту модель?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_model(model_id)
                self.refresh_data()
                QMessageBox.information(self, "Успех", "Модель удалена!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")
    
    def manage_prices(self, model_id, model_name):
        """Управление ценами модели"""
        dialog = PriceDialog(self, model_id, model_name)
        dialog.exec()
        self.refresh_data()
    
    def search_models(self, text):
        """Поиск моделей"""
        self.load_models(text)
    
    def update_statistics(self):
        """Обновление статистики"""
        try:
            stats = self.db.get_price_statistics()
            
            stats_text = "📊 СТАТИСТИКА ЦЕН ПО РЕГИОНАМ\n" + "="*60 + "\n\n"
            
            for stat in stats:
                region_name = stat['region_name']
                currency_code, currency_symbol = CURRENCY_MAP.get(region_name, ('USD', '$'))
                
                stats_text += f"🌍 {region_name} ({currency_code}):\n"
                stats_text += f"   • Моделей с ценами: {stat['models_count']}\n"
                stats_text += f"   • Средняя цена: {currency_symbol}{stat['avg_price']:,.2f}\n"
                stats_text += f"   • Минимальная цена: {currency_symbol}{stat['min_price']:,.2f}\n"
                stats_text += f"   • Максимальная цена: {currency_symbol}{stat['max_price']:,.2f}\n\n"
            
            self.stats_text.setText(stats_text)
        except Exception as e:
            self.stats_text.setText(f"Ошибка при загрузке статистики: {str(e)}")
    
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        self.db.disconnect()
        event.accept()