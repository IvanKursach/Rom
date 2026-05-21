function showLoginModal() { document.getElementById('login-modal').style.display = 'block'; }
function showRegisterModal() { document.getElementById('register-modal').style.display = 'block'; }
function closeModal(id) { document.getElementById(id).style.display = 'none'; }
function showMessage(title, text) {
    document.getElementById('message-title').textContent = title;
    document.getElementById('message-text').textContent = text;
    document.getElementById('message-modal').style.display = 'block';
}

// Регистрация
document.getElementById('register-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = { name: document.getElementById('reg-name').value, email: document.getElementById('reg-email').value, password: document.getElementById('reg-password').value, phone: document.getElementById('reg-phone').value };
    if (data.password.length < 6) { showMessage('Ошибка', 'Пароль минимум 6 символов'); return; }
    const res = await fetch('/api/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
    const result = await res.json();
    if (res.ok) { showMessage('Успех', 'Регистрация успешна! Войдите.'); closeModal('register-modal'); showLoginModal(); }
    else showMessage('Ошибка', result.error);
});

// Логин
document.getElementById('login-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = { email: document.getElementById('login-email').value, password: document.getElementById('login-password').value };
    const res = await fetch('/api/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
    const result = await res.json();
    if (res.ok) { location.reload(); }
    else showMessage('Ошибка', result.error);
});

// Выход
async function logout() { await fetch('/api/logout', { method: 'POST' }); location.reload(); }

// Запись на тренировку
async function bookTraining(id, name) {
    const res = await fetch('/api/book', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ training_id: id }) });
    const result = await res.json();
    if (res.ok) showMessage('Успех', `Вы записаны на "${name}"!`);
    else showMessage('Ошибка', result.error);
}

// Отмена записи
async function cancelBooking(id) {
    if (!confirm('Отменить запись?')) return;
    const res = await fetch(`/api/cancel/${id}`, { method: 'DELETE' });
    if (res.ok) location.reload();
    else showMessage('Ошибка', 'Не удалось отменить');
}

// Редактирование профиля
async function updateProfile() {
    const name = prompt('Новое имя:', document.getElementById('profile-name')?.textContent);
    const phone = prompt('Новый телефон:', document.getElementById('profile-phone')?.textContent);
    if (name) {
        await fetch('/api/profile', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, phone }) });
        location.reload();
    }
}

// Покупка абонемента
async function buyMembership(type) {
    const res = await fetch('/api/buy-membership', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ membership_type: type }) });
    if (res.ok) showMessage('Успех', 'Абонемент приобретен!');
    else showMessage('Ошибка', 'Ошибка при покупке');
}