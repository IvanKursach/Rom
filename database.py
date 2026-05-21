import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DB', 'rom_krs')
}

def create_tables():
    print("=" * 50)
    print("🚀 Создание таблиц Fitness Club")
    print("=" * 50)
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Удаляем старые таблицы если есть
        print("🗑️ Очищаем старые таблицы...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("DROP TABLE IF EXISTS bookings")
        cursor.execute("DROP TABLE IF EXISTS trainings")
        cursor.execute("DROP TABLE IF EXISTS prices")
        cursor.execute("DROP TABLE IF EXISTS trainers")
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # Таблица users
        print("📀 Создаем таблицы...")
        cursor.execute("""
            CREATE TABLE users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                phone VARCHAR(20),
                membership VARCHAR(20) DEFAULT 'basic',
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("   ✅ Таблица users создана")
        
        # Таблица trainers
        cursor.execute("""
            CREATE TABLE trainers (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                specialization VARCHAR(200),
                experience INT,
                bio TEXT,
                photo_url VARCHAR(500),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("   ✅ Таблица trainers создана")
        
        # Таблица trainings
        cursor.execute("""
            CREATE TABLE trainings (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                trainer_id INT,
                trainer_name VARCHAR(100),
                max_people INT DEFAULT 20,
                duration INT DEFAULT 60,
                day VARCHAR(20),
                time TIME,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (trainer_id) REFERENCES trainers(id) ON DELETE SET NULL
            )
        """)
        print("   ✅ Таблица trainings создана")
        
        # Таблица prices
        cursor.execute("""
            CREATE TABLE prices (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                price INT NOT NULL,
                days INT NOT NULL,
                features TEXT,
                is_popular BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("   ✅ Таблица prices создана")
        
        # Таблица bookings
        cursor.execute("""
            CREATE TABLE bookings (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                training_id INT NOT NULL,
                booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'active',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (training_id) REFERENCES trainings(id) ON DELETE CASCADE,
                UNIQUE KEY unique_booking (user_id, training_id)
            )
        """)
        print("   ✅ Таблица bookings создана")
        
        # ============================================
        # ЗАГРУЗКА ДАННЫХ ИЗ ФАЙЛА data.sql
        # ============================================
        print("-" * 50)
        print("📀 Загрузка данных...")
        
        # Добавляем тренеров
        print("   📀 Добавляем тренеров...")
        try:
            cursor.execute("""
                INSERT INTO trainers (name, specialization, experience, bio, photo_url) VALUES
                ('Анна Иванова', 'Йога, Пилатес, Медитация', 8, 'Сертифицированный инструктор по йоге с 8-летним опытом. Специализируется на хатха-йоге, йога-нидре и медитации. Помогает найти гармонию тела и духа, снять стресс и улучшить гибкость.', '/static/trainers/anna.jpg'),
                ('Петр Сидоров', 'Силовые тренировки, CrossFit, Пауэрлифтинг', 10, 'Мастер спорта по пауэрлифтингу. Кандидат в мастера спорта по CrossFit. Тренирует чемпионов области и города. Специализируется на наборе мышечной массы и силовых показателях.', '/static/trainers/petr.jpg'),
                ('Елена Прекрасная', 'Функциональный тренинг, Стретчинг, TRX', 6, 'Эксперт по функциональному тренингу и восстановлению после травм. Сертифицированный тренер по TRX и стретчингу. Помогает улучшить подвижность суставов и укрепить мышцы кора.', '/static/trainers/elena.jpg'),
                ('Майк Тайсон', 'Бокс, Единоборства, Самооборона', 15, 'Профессиональный боксер, мастер спорта международного класса. Тренер по боксу и самообороне. Научит защищать себя и держать форму. Проводит спарринги и тренировки на реакцию.', '/static/trainers/mike.jpg'),
                ('Мария Кармен', 'Зумба, Танцы, Аэробика, Латина', 5, 'Энергичный тренер по зумбе и латиноамериканским танцам. Чемпионка по танцевальному спорту. Зарядит позитивом на всю неделю и поможет похудеть в удовольствие.', '/static/trainers/maria.jpg'),
                ('Дмитрий Волков', 'Кроссфит, Воркаут, Гимнастика', 7, 'Мастер спорта по спортивной гимнастике. Специализируется на функциональном тренинге и работе с собственным весом. Поможет развить выносливость и координацию.', '/static/trainers/dmitry.jpg'),
                ('Ольга Смирнова', 'Пилатес, Бодифлекс, Оздоровительная гимнастика', 9, 'Сертифицированный инструктор по пилатесу и бодифлексу. Специализируется на коррекции осанки и оздоровлении позвоночника. Поможет укрепить мышцы кора и улучшить осанку.', '/static/trainers/olga.jpg'),
                ('Алексей Морозов', 'Тайский бокс, ММА, Самооборона', 12, 'Мастер спорта по тайскому боксу. Тренер по смешанным единоборствам. Проводит тренировки по самообороне для всех возрастов.', '/static/trainers/alexey.jpg')
            """)
            conn.commit()
            print("   ✅ Тренеры добавлены")
        except Error as e:
            if 'Duplicate' not in str(e):
                print(f"   ⚠️ Ошибка при добавлении тренеров: {e}")
        
        # Добавляем тренировки
        print("   📀 Добавляем тренировки...")
        try:
            cursor.execute("""
                INSERT INTO trainings (name, description, trainer_name, max_people, duration, day, time, is_active) VALUES
                ('Хатха Йога', 'Классическая хатха-йога для начинающих и продолжающих. Включает асаны, пранаяму и медитацию. Подходит для всех уровней подготовки.', 'Анна Иванова', 15, 60, 'monday', '08:00:00', 1),
                ('Силовая тренировка', 'Интенсивный воркаут для набора мышечной массы. Работа со штангой, гантелями и тренажерами.', 'Петр Сидоров', 20, 60, 'tuesday', '18:00:00', 1),
                ('CrossFit WOD', 'Высокоинтенсивный функциональный тренинг. Каждый день новая программа (WOD).', 'Петр Сидоров', 12, 50, 'wednesday', '19:00:00', 1),
                ('Пилатес', 'Классический пилатес на матах. Укрепление мышц кора и улучшение осанки.', 'Ольга Смирнова', 15, 55, 'thursday', '11:00:00', 1),
                ('Zumba Fitness', 'Танцевальная фитнес-программа в стиле латино. Весело и эффективно!', 'Мария Кармен', 25, 60, 'friday', '19:00:00', 1),
                ('Бокс', 'Обучение технике бокса: удары, защита, передвижения. Спарринги по желанию.', 'Майк Тайсон', 10, 60, 'monday', '20:00:00', 1),
                ('Кроссфит', 'Интенсивные тренировки с элементами гимнастики, тяжелой атлетики.', 'Дмитрий Волков', 15, 60, 'tuesday', '19:00:00', 1),
                ('Стретчинг', 'Растяжка всего тела. Улучшение гибкости и подвижности суставов.', 'Елена Прекрасная', 20, 45, 'wednesday', '20:00:00', 1)
            """)
            conn.commit()
            print("   ✅ Тренировки добавлены")
        except Error as e:
            if 'Duplicate' not in str(e):
                print(f"   ⚠️ Ошибка при добавлении тренировок: {e}")
        
        # Добавляем цены
        print("   📀 Добавляем цены...")
        try:
            cursor.execute("""
                INSERT INTO prices (name, price, days, features, is_popular, is_active) VALUES
                ('Разовое посещение', 500, 1, 'Одна тренировка, тренажерный зал, раздевалка, душ', 0, 1),
                ('Базовый', 3000, 30, '8 тренировок, тренажерный зал, раздевалка, душ', 0, 1),
                ('Премиум', 5000, 30, 'Безлимит тренировок, тренажерный зал, сауна, солярий, парковка', 1, 1),
                ('VIP', 12000, 90, 'Безлимит на 3 месяца, персональный тренер, тренажерный зал, сауна, солярий, бассейн, парковка, шкафчик', 0, 1)
            """)
            conn.commit()
            print("   ✅ Цены добавлены")
        except Error as e:
            if 'Duplicate' not in str(e):
                print(f"   ⚠️ Ошибка при добавлении цен: {e}")
        
        # Добавляем админа (пароль: admin123)
        print("   📀 Добавляем администратора...")
        try:
            cursor.execute("""
                INSERT INTO users (name, email, password, phone, membership, is_admin) VALUES
                ('Администратор', 'admin@fit.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYrJvY6xJ/96', '+79990000000', 'vip', 1)
            """)
            conn.commit()
            print("   ✅ Администратор добавлен")
        except Error as e:
            if 'Duplicate' not in str(e):
                print(f"   ⚠️ Ошибка при добавлении администратора: {e}")
        
        # ============================================
        # ПРОВЕРКА РЕЗУЛЬТАТА
        # ============================================
        print("-" * 50)
        print("📊 Проверка базы данных:")
        
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"   ✅ Всего таблиц: {len(tables)}")
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"   📁 {table[0]}: {count} записей")
        
        cursor.close()
        conn.close()
        
        print("-" * 50)
        print("✅ База данных готова!")
        print("👤 Админ: admin@fit.com / admin123")
        print("👉 Запусти: python app.py")
        
    except Error as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    create_tables()