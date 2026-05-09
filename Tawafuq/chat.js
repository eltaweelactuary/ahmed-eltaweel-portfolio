import { FIREBASE_CONFIG } from './config.js';

// Initialize Firebase
if (!firebase.apps.length) {
    firebase.initializeApp(FIREBASE_CONFIG);
}

const auth = firebase.auth();
const db = firebase.database();

document.addEventListener('DOMContentLoaded', () => {
    const messagesArea = document.getElementById('messagesArea');
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const userNameDisplay = document.getElementById('userNameDisplay');
    const backToHome = document.getElementById('backToHome');

    // Check Auth State
    auth.onAuthStateChanged(user => {
        if (user) {
            userNameDisplay.textContent = user.displayName || user.email;
            loadMessages();
        } else {
            // Redirect to index if not logged in
            window.location.href = 'index.html';
        }
    });

    backToHome.addEventListener('click', () => {
        window.location.href = 'index.html';
    });

    // Load Messages from Firebase
    const loadMessages = () => {
        const messagesRef = db.ref('messages/global'); // Simple global room for demo
        messagesRef.on('child_added', snapshot => {
            const msg = snapshot.val();
            appendMessage(msg.text, msg.uid === auth.currentUser.uid ? 'sent' : 'received');
        });
    };

    // Send Message
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = messageInput.value.trim();
        if (text && auth.currentUser) {
            db.ref('messages/global').push({
                text: text,
                uid: auth.currentUser.uid,
                timestamp: Date.now()
            });
            messageInput.value = '';
        }
    });

    const appendMessage = (text, type) => {
        const div = document.createElement('div');
        div.className = `message ${type}`;
        div.textContent = text;
        messagesArea.appendChild(div);
        messagesArea.scrollTop = messagesArea.scrollHeight;
    };
});
