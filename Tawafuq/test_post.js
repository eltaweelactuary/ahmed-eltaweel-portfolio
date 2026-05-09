const targetUrl = 'https://script.google.com/macros/s/AKfycbzv5hX71jQfvGLK3cHyYv84ECb9rEaR1nwgHMqMkeHQ4ttSXdpzIjYk80xa70RaywpqiQ/exec';
const data = {
    name: 'اختبار دبلوي',
    email: 'test@test.com',
    gender: 'ذكر',
    job: 'مبرمج',
    whatsapp: '01000000',
    bio: 'هذا اختبار من بيئة التطوير'
};

fetch(targetUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'text/plain' },
    body: JSON.stringify(data)
})
.then(res => res.text())
.then(text => console.log('Response:', text))
.catch(err => console.error('Error:', err));
