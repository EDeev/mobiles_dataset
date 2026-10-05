# db/database.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class Database:
    """
    Класс для управления подключением к PostgreSQL и выполнения операций
    Использует паттерн Singleton для единственного экземпляра подключения
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, host=None, port=None, database=None, user=None, password=None):
        # Параметры подключения: аргументы, затем переменные окружения DB_*, затем значения для локальной разработки
        host = host or os.environ.get('DB_HOST', 'localhost')
        port = port or int(os.environ.get('DB_PORT', '5432'))
        database = database or os.environ.get('DB_NAME', 'mobile_devices_db')
        user = user or os.environ.get('DB_USER', 'admin')
        password = password or os.environ.get('DB_PASSWORD', 'password')
        if not hasattr(self, 'initialized'):
            self.connection_params = {
                'host': host,
                'port': port,
                'database': database,
                'user': user,
                'password': password
            }
            self.connection = None
            self.initialized = True
    
    def connect(self):
        """Установка соединения с БД"""
        try:
            self.connection = psycopg2.connect(**self.connection_params)
            logger.info("✅ Подключение к БД установлено")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            return False
    
    def disconnect(self):
        """Закрытие соединения с БД"""
        if self.connection:
            self.connection.close()
            logger.info("🔒 Соединение с БД закрыто")
    
    @contextmanager
    def get_cursor(self, dict_cursor=True):
        """
        Контекстный менеджер для безопасной работы с курсором
        """
        cursor_factory = RealDictCursor if dict_cursor else None
        cursor = self.connection.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"❌ Ошибка выполнения запроса: {e}")
            raise
        finally:
            cursor.close()
    
    # === CRUD операции для Companies ===
    
    def get_all_companies(self) -> List[Dict[str, Any]]:
        """Получение всех компаний"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT c.company_id, c.company_name, COUNT(m.model_id) as models_count
                FROM companies c
                LEFT JOIN models m ON c.company_id = m.company_id
                GROUP BY c.company_id, c.company_name
                ORDER BY c.company_name
            """)
            return cursor.fetchall()
    
    def add_company(self, company_name: str) -> int:
        """Добавление новой компании"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO companies (company_name) VALUES (%s) RETURNING company_id",
                (company_name,)
            )
            return cursor.fetchone()['company_id']
    
    def update_company(self, company_id: int, company_name: str):
        """Обновление названия компании"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "UPDATE companies SET company_name = %s WHERE company_id = %s",
                (company_name, company_id)
            )
    
    def delete_company(self, company_id: int):
        """Удаление компании (каскадно удалит все модели)"""
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM companies WHERE company_id = %s", (company_id,))
    
    # === CRUD операции для Models ===
    
    def get_all_models(self, company_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Получение всех моделей (опционально по компании)"""
        query = """
            SELECT 
                m.model_id, m.model_name, c.company_name, 
                m.mobile_weight, m.ram, m.front_camera, 
                m.back_camera, pr.processor_name, m.battery_capacity, 
                m.screen_size, m.launched_year,
                COUNT(DISTINCT p.region_id) as price_regions
            FROM models m
            JOIN companies c ON m.company_id = c.company_id
            LEFT JOIN processors pr ON m.processor_id = pr.processor_id
            LEFT JOIN prices p ON m.model_id = p.model_id
        """
        
        params = []
        if company_id:
            query += " WHERE m.company_id = %s"
            params.append(company_id)
        
        query += " GROUP BY m.model_id, c.company_name, pr.processor_name ORDER BY c.company_name, m.model_name"
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def get_model_by_id(self, model_id: int) -> Dict[str, Any]:
        """Получение модели по ID"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT m.*, c.company_name, pr.processor_name
                FROM models m
                JOIN companies c ON m.company_id = c.company_id
                LEFT JOIN processors pr ON m.processor_id = pr.processor_id
                WHERE m.model_id = %s
            """, (model_id,))
            return cursor.fetchone()
    
    def add_model(self, model_data: Dict[str, Any]) -> int:
        """Добавление новой модели"""
        # Сначала получаем или создаем процессор
        processor_id = None
        if model_data.get('processor_name'):
            processor_id = self.get_or_create_processor(model_data['processor_name'])
        
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO models 
                (model_name, company_id, processor_id, mobile_weight, 
                 ram, front_camera, back_camera, battery_capacity, 
                 screen_size, launched_year)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING model_id
            """, (
                model_data['model_name'],
                model_data['company_id'],
                processor_id,
                model_data.get('mobile_weight'),
                model_data.get('ram'),
                model_data.get('front_camera'),
                model_data.get('back_camera'),
                model_data.get('battery_capacity'),
                model_data.get('screen_size'),
                model_data.get('launched_year')
            ))
            return cursor.fetchone()['model_id']
    
    def update_model(self, model_id: int, model_data: Dict[str, Any]):
        """Обновление модели"""
        # Получаем или создаем процессор
        processor_id = None
        if model_data.get('processor_name'):
            processor_id = self.get_or_create_processor(model_data['processor_name'])
        
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE models SET
                    model_name = %s,
                    company_id = %s,
                    processor_id = %s,
                    mobile_weight = %s,
                    ram = %s,
                    front_camera = %s,
                    back_camera = %s,
                    battery_capacity = %s,
                    screen_size = %s,
                    launched_year = %s
                WHERE model_id = %s
            """, (
                model_data['model_name'],
                model_data['company_id'],
                processor_id,
                model_data.get('mobile_weight'),
                model_data.get('ram'),
                model_data.get('front_camera'),
                model_data.get('back_camera'),
                model_data.get('battery_capacity'),
                model_data.get('screen_size'),
                model_data.get('launched_year'),
                model_id
            ))
    
    def delete_model(self, model_id: int):
        """Удаление модели"""
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM models WHERE model_id = %s", (model_id,))
    
    # === CRUD операции для Prices ===
    
    def get_model_prices(self, model_id: int) -> List[Dict[str, Any]]:
        """Получение всех цен для модели"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.price_id, p.model_id, p.region_id, 
                       r.region_name, p.price, p.currency
                FROM prices p
                JOIN regions r ON p.region_id = r.region_id
                WHERE p.model_id = %s
                ORDER BY r.region_name
            """, (model_id,))
            return cursor.fetchall()
    
    def add_or_update_price(self, model_id: int, region_id: int, price: float):
        """Добавление или обновление цены"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO prices (model_id, region_id, price)
                VALUES (%s, %s, %s)
                ON CONFLICT (model_id, region_id) 
                DO UPDATE SET price = EXCLUDED.price
            """, (model_id, region_id, price))
    
    def delete_price(self, price_id: int):
        """Удаление цены"""
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM prices WHERE price_id = %s", (price_id,))
    
    # === Вспомогательные методы ===
    
    def get_or_create_processor(self, processor_name: str) -> int:
        """Получение или создание процессора"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT processor_id FROM processors WHERE processor_name = %s",
                (processor_name,)
            )
            result = cursor.fetchone()
            
            if result:
                return result['processor_id']
            else:
                cursor.execute(
                    "INSERT INTO processors (processor_name) VALUES (%s) RETURNING processor_id",
                    (processor_name,)
                )
                return cursor.fetchone()['processor_id']
    
    def get_all_regions(self) -> List[Dict[str, Any]]:
        """Получение всех регионов"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM regions ORDER BY region_name")
            return cursor.fetchall()
    
    def get_all_processors(self) -> List[Dict[str, Any]]:
        """Получение всех процессоров"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM processors ORDER BY processor_name")
            return cursor.fetchall()
    
    # === Методы для аналитики ===
    
    def get_price_statistics(self) -> List[Dict[str, Any]]:
        """Получение статистики цен по регионам"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    r.region_name,
                    COUNT(p.price_id) as models_count,
                    AVG(p.price) as avg_price,
                    MIN(p.price) as min_price,
                    MAX(p.price) as max_price
                FROM prices p
                JOIN regions r ON p.region_id = r.region_id
                GROUP BY r.region_name
                ORDER BY avg_price DESC
            """)
            return cursor.fetchall()
    
    def search_models(self, search_text: str) -> List[Dict[str, Any]]:
        """Поиск моделей по тексту"""
        search_pattern = f"%{search_text}%"
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT
                    m.model_id, m.model_name, c.company_name,
                    m.ram, m.battery_capacity, m.launched_year
                FROM models m
                JOIN companies c ON m.company_id = c.company_id
                WHERE 
                    m.model_name ILIKE %s OR
                    c.company_name ILIKE %s OR
                    m.ram ILIKE %s OR
                    m.battery_capacity ILIKE %s
                ORDER BY c.company_name, m.model_name
                LIMIT 100
            """, (search_pattern, search_pattern, search_pattern, search_pattern))
            return cursor.fetchall()