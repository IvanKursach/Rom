from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import bcrypt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'secret')

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DB')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = None
login_manager.login_message = None

# ========== МОДЕЛИ ==========

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    membership = db.Column(db.String(20), default='basic')
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Trainer(db.Model):
    __tablename__ = 'trainers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(200))
    experience = db.Column(db.Integer)
    bio = db.Column(db.Text)
    photo_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Training(db.Model):
    __tablename__ = 'trainings'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    trainer_id = db.Column(db.Integer, db.ForeignKey('trainers.id'))
    trainer_name = db.Column(db.String(100))
    max_people = db.Column(db.Integer, default=20)
    duration = db.Column(db.Integer, default=60)
    day = db.Column(db.String(20))
    time = db.Column(db.Time)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    training_id = db.Column(db.Integer, db.ForeignKey('trainings.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default='active')

class Price(db.Model):
    __tablename__ = 'prices'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    days = db.Column(db.Integer, nullable=False)
    features = db.Column(db.Text)
    is_popular = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({'error': 'Требуется авторизация'}), 401

# ========== СТРАНИЦЫ ==========

@app.route('/')
def index():
    trainings = Training.query.filter_by(is_active=True).limit(4).all()
    return render_template('index.html', trainings=trainings)

@app.route('/schedule')
def schedule():
    trainings = Training.query.filter_by(is_active=True).all()
    return render_template('schedule.html', trainings=trainings)

@app.route('/trainers')
def trainers():
    trainers = Trainer.query.filter_by(is_active=True).all()
    return render_template('trainers.html', trainers=trainers)

@app.route('/prices')
def prices():
    prices = Price.query.filter_by(is_active=True).all()
    return render_template('prices.html', prices=prices)

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

@app.route('/profile')
@login_required
def profile():
    bookings = db.session.query(Booking, Training).join(Training, Booking.training_id == Training.id).filter(Booking.user_id == current_user.id, Booking.status == 'active').all()
    return render_template('profile.html', bookings=bookings)

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    return render_template('admin.html')

# ========== API ==========

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email уже существует'}), 400
    
    hashed = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt())
    user = User(name=data['name'], email=data['email'], password=hashed.decode(), phone=data.get('phone', ''))
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Регистрация успешна'})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user and bcrypt.checkpw(data['password'].encode(), user.password.encode()):
        login_user(user)
        return jsonify({'message': 'Вход выполнен', 'user': {'id': user.id, 'name': user.name, 'email': user.email, 'is_admin': user.is_admin}})
    return jsonify({'error': 'Неверный email или пароль'}), 401

@app.route('/api/check-auth')
@login_required
def check_auth():
    return jsonify({
        'authenticated': True,
        'is_admin': current_user.is_admin,
        'user': {
            'id': current_user.id,
            'name': current_user.name,
            'email': current_user.email,
            'is_admin': current_user.is_admin
        }
    })

@app.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    logout_user()
    return jsonify({'message': 'Выход выполнен'})

@app.route('/api/book', methods=['POST'])
@login_required
def api_book():
    data = request.json
    training_id = data.get('training_id')
    
    training = Training.query.get(training_id)
    if not training:
        return jsonify({'error': 'Тренировка не найдена'}), 404
    
    existing = Booking.query.filter_by(user_id=current_user.id, training_id=training_id, status='active').first()
    if existing:
        return jsonify({'error': 'Вы уже записаны'}), 400
    
    bookings_count = Booking.query.filter_by(training_id=training_id, status='active').count()
    if bookings_count >= training.max_people:
        return jsonify({'error': 'Нет свободных мест'}), 400
    
    booking = Booking(user_id=current_user.id, training_id=training_id)
    db.session.add(booking)
    db.session.commit()
    return jsonify({'message': 'Запись успешна'})

@app.route('/api/cancel/<int:booking_id>', methods=['DELETE'])
@login_required
def api_cancel(booking_id):
    booking = Booking.query.get(booking_id)
    if booking and booking.user_id == current_user.id:
        booking.status = 'cancelled'
        db.session.commit()
        return jsonify({'message': 'Запись отменена'})
    return jsonify({'error': 'Не найдено'}), 404

@app.route('/api/profile', methods=['PUT'])
@login_required
def api_profile():
    data = request.json
    current_user.name = data.get('name', current_user.name)
    current_user.phone = data.get('phone', current_user.phone)
    db.session.commit()
    return jsonify({'message': 'Профиль обновлен'})

@app.route('/api/buy-membership', methods=['POST'])
@login_required
def api_buy_membership():
    data = request.json
    current_user.membership = data.get('membership_type', 'basic')
    db.session.commit()
    return jsonify({'message': 'Абонемент приобретен'})

@app.route('/api/trainings')
def api_trainings():
    try:
        trainings = Training.query.filter_by(is_active=True).all()
        result = []
        for t in trainings:
            result.append({
                'id': t.id,
                'name': t.name,
                'description': t.description,
                'trainer_name': t.trainer_name,
                'max_people': t.max_people,
                'duration': t.duration,
                'day': t.day,
                'time': t.time.strftime('%H:%M') if t.time else None,
                'is_active': t.is_active
            })
        return jsonify(result)
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify([]), 500
    
# ========== АДМИН СТАТИСТИКА ==========

@app.route('/api/admin/stats')
@login_required
def api_admin_stats():
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    # Основная статистика
    total_users = User.query.count()
    total_trainings = Training.query.filter_by(is_active=True).count()
    total_bookings = Booking.query.filter_by(status='active').count()
    total_trainers = Trainer.query.filter_by(is_active=True).count()
    
    # Статистика по абонементам
    basic_users = User.query.filter_by(membership='basic').count()
    premium_users = User.query.filter_by(membership='premium').count()
    vip_users = User.query.filter_by(membership='vip').count()
    
    # Статистика по дням недели
    from sqlalchemy import func
    bookings_by_day = db.session.query(
        Training.day, func.count(Booking.id)
    ).join(Booking, Booking.training_id == Training.id).filter(Booking.status == 'active').group_by(Training.day).all()
    
    days_order = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6}
    bookings_by_day = sorted(bookings_by_day, key=lambda x: days_order.get(x[0], 7))
    
    # Популярные тренировки
    popular_trainings = db.session.query(
        Training.name, func.count(Booking.id).label('count')
    ).join(Booking, Booking.training_id == Training.id).filter(Booking.status == 'active').group_by(Training.id).order_by(func.count(Booking.id).desc()).limit(5).all()
    
    # Недавние бронирования
    recent_bookings = db.session.query(
        Booking, User, Training
    ).join(User, Booking.user_id == User.id).join(Training, Booking.training_id == Training.id).filter(Booking.status == 'active').order_by(Booking.booking_date.desc()).limit(10).all()
    
    # Статистика за последние 7 дней
    last_week = datetime.now() - timedelta(days=7)
    bookings_last_week = Booking.query.filter(Booking.booking_date >= last_week).count()
    
    # Доход (примерный, на основе абонементов)
    membership_prices = {'basic': 3000, 'premium': 5000, 'vip': 12000}
    estimated_revenue = basic_users * membership_prices['basic'] + premium_users * membership_prices['premium'] + vip_users * membership_prices['vip']
    
    return jsonify({
        'total_users': total_users,
        'total_trainings': total_trainings,
        'total_bookings': total_bookings,
        'total_trainers': total_trainers,
        'basic_users': basic_users,
        'premium_users': premium_users,
        'vip_users': vip_users,
        'bookings_by_day': [{'day': day, 'count': count} for day, count in bookings_by_day],
        'popular_trainings': [{'name': name, 'count': count} for name, count in popular_trainings],
        'recent_bookings': [{
            'id': b.id,
            'user_name': u.name,
            'training_name': t.name,
            'date': b.booking_date.strftime('%d.%m.%Y %H:%M')
        } for b, u, t in recent_bookings],
        'bookings_last_week': bookings_last_week,
        'estimated_revenue': estimated_revenue
    })

# ========== АДМИН CRUD ДЛЯ ТРЕНИРОВОК ==========

@app.route('/api/admin/trainings')
@login_required
def api_admin_trainings():
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    trainings = Training.query.all()
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'description': t.description,
        'trainer_name': t.trainer_name,
        'max_people': t.max_people,
        'duration': t.duration,
        'day': t.day,
        'time': t.time.strftime('%H:%M') if t.time else None,
        'is_active': t.is_active
    } for t in trainings])

@app.route('/api/admin/training', methods=['POST'])
@login_required
def api_admin_training_create():
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    data = request.json
    training = Training(
        name=data['name'],
        description=data.get('description', ''),
        trainer_name=data['trainer_name'],
        max_people=data.get('max_people', 20),
        duration=data.get('duration', 60),
        day=data['day'],
        time=datetime.strptime(data['time'], '%H:%M').time() if data.get('time') else None,
        is_active=data.get('is_active', True)
    )
    db.session.add(training)
    db.session.commit()
    return jsonify({'message': 'Тренировка добавлена', 'id': training.id})

@app.route('/api/admin/training/<int:id>', methods=['PUT'])
@login_required
def api_admin_training_update(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    training = Training.query.get(id)
    if not training:
        return jsonify({'error': 'Тренировка не найдена'}), 404
    
    data = request.json
    training.name = data.get('name', training.name)
    training.description = data.get('description', training.description)
    training.trainer_name = data.get('trainer_name', training.trainer_name)
    training.max_people = data.get('max_people', training.max_people)
    training.duration = data.get('duration', training.duration)
    training.day = data.get('day', training.day)
    training.time = datetime.strptime(data['time'], '%H:%M').time() if data.get('time') else training.time
    training.is_active = data.get('is_active', training.is_active)
    db.session.commit()
    return jsonify({'message': 'Тренировка обновлена'})

@app.route('/api/admin/training/<int:id>', methods=['DELETE'])
@login_required
def api_admin_training_delete(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    Booking.query.filter_by(training_id=id).delete()
    Training.query.filter_by(id=id).delete()
    db.session.commit()
    return jsonify({'message': 'Тренировка удалена'})

# ========== АДМИН CRUD ДЛЯ ТРЕНЕРОВ ==========

@app.route('/api/admin/trainers')
@login_required
def api_admin_trainers():
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    trainers = Trainer.query.all()
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'specialization': t.specialization,
        'experience': t.experience,
        'bio': t.bio,
        'photo_url': t.photo_url,
        'is_active': t.is_active
    } for t in trainers])

@app.route('/api/admin/trainer', methods=['POST'])
@login_required
def api_admin_trainer_create():
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    data = request.json
    trainer = Trainer(
        name=data['name'],
        specialization=data.get('specialization', ''),
        experience=data.get('experience', 0),
        bio=data.get('bio', ''),
        photo_url=data.get('photo_url', ''),
        is_active=data.get('is_active', True)
    )
    db.session.add(trainer)
    db.session.commit()
    return jsonify({'message': 'Тренер добавлен', 'id': trainer.id})

@app.route('/api/admin/trainer/<int:id>', methods=['PUT'])
@login_required
def api_admin_trainer_update(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    trainer = Trainer.query.get(id)
    if not trainer:
        return jsonify({'error': 'Тренер не найден'}), 404
    
    data = request.json
    trainer.name = data.get('name', trainer.name)
    trainer.specialization = data.get('specialization', trainer.specialization)
    trainer.experience = data.get('experience', trainer.experience)
    trainer.bio = data.get('bio', trainer.bio)
    trainer.photo_url = data.get('photo_url', trainer.photo_url)
    trainer.is_active = data.get('is_active', trainer.is_active)
    db.session.commit()
    return jsonify({'message': 'Тренер обновлен'})

@app.route('/api/admin/trainer/<int:id>', methods=['DELETE'])
@login_required
def api_admin_trainer_delete(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    trainer = Trainer.query.get(id)
    if trainer:
        db.session.delete(trainer)
        db.session.commit()
    return jsonify({'message': 'Тренер удален'})

# ========== АДМИН CRUD ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ==========

@app.route('/api/admin/users')
@login_required
def api_admin_users():
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'name': u.name,
        'email': u.email,
        'phone': u.phone,
        'membership': u.membership,
        'is_admin': u.is_admin,
        'created_at': u.created_at.strftime('%d.%m.%Y')
    } for u in users])

@app.route('/api/admin/user/<int:id>', methods=['PUT'])
@login_required
def api_admin_user_update(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    user = User.query.get(id)
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    data = request.json
    user.membership = data.get('membership', user.membership)
    user.is_admin = data.get('is_admin', user.is_admin)
    db.session.commit()
    return jsonify({'message': 'Пользователь обновлен'})

@app.route('/api/admin/user/<int:id>', methods=['DELETE'])
@login_required
def api_admin_user_delete(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    Booking.query.filter_by(user_id=id).delete()
    User.query.filter_by(id=id).delete()
    db.session.commit()
    return jsonify({'message': 'Пользователь удален'})

# ========== АДМИН CRUD ДЛЯ ЦЕН ==========

@app.route('/api/admin/prices')
@login_required
def api_admin_prices():
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    prices = Price.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': p.price,
        'days': p.days,
        'features': p.features,
        'is_popular': p.is_popular,
        'is_active': p.is_active
    } for p in prices])

@app.route('/api/admin/price', methods=['POST'])
@login_required
def api_admin_price_create():
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    data = request.json
    price = Price(
        name=data['name'],
        price=data['price'],
        days=data['days'],
        features=data.get('features', ''),
        is_popular=data.get('is_popular', False),
        is_active=data.get('is_active', True)
    )
    db.session.add(price)
    db.session.commit()
    return jsonify({'message': 'Цена добавлена', 'id': price.id})

@app.route('/api/admin/price/<int:id>', methods=['PUT'])
@login_required
def api_admin_price_update(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    price = Price.query.get(id)
    if not price:
        return jsonify({'error': 'Цена не найдена'}), 404
    
    data = request.json
    price.name = data.get('name', price.name)
    price.price = data.get('price', price.price)
    price.days = data.get('days', price.days)
    price.features = data.get('features', price.features)
    price.is_popular = data.get('is_popular', price.is_popular)
    price.is_active = data.get('is_active', price.is_active)
    db.session.commit()
    return jsonify({'message': 'Цена обновлена'})

@app.route('/api/admin/price/<int:id>', methods=['DELETE'])
@login_required
def api_admin_price_delete(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    Price.query.filter_by(id=id).delete()
    db.session.commit()
    return jsonify({'message': 'Цена удалена'})

# ========== АДМИН БРОНИРОВАНИЯ ==========

@app.route('/api/admin/bookings')
@login_required
def api_admin_bookings():
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    bookings = db.session.query(
        Booking, User, Training
    ).join(User, Booking.user_id == User.id).join(Training, Booking.training_id == Training.id).order_by(Booking.booking_date.desc()).all()
    return jsonify([{
        'id': b.id,
        'user_name': u.name,
        'user_email': u.email,
        'training_name': t.name,
        'booking_date': b.booking_date.strftime('%d.%m.%Y %H:%M'),
        'status': b.status
    } for b, u, t in bookings])

@app.route('/api/admin/booking/<int:id>', methods=['DELETE'])
@login_required
def api_admin_booking_delete(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    Booking.query.filter_by(id=id).delete()
    db.session.commit()
    return jsonify({'message': 'Бронирование удалено'})

@app.route('/api/check-admin')
@login_required
def check_admin():
    if current_user.is_admin:
        return jsonify({'is_admin': True})
    return jsonify({'error': 'Доступ запрещен'}), 403

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Railway передает порт через переменную окружения PORT
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)