// Tawafuq Configuration

export const CONFIG = {
    // The specific Google Form provided by the user
    // Using /viewform ensures users see the form, not the editor
    googleFormUrl: "https://docs.google.com/forms/d/1KwTzfs5yG793G9ufGCs5HydqYkw1nJ62tZEhs7DnQaE/viewform",
    
    // Spreadsheet ID attached to the Google Form
    spreadsheetId: "1-Wlq_U6T-y-i2mR6yWf8PqI6bY9v-02E0p6E2o8P_E", // Example or user's ID
    sheetGid: "0",
    
    // The Web App URL from Google Apps Script (User needs to paste this after deployment)
    googleScriptUrl: "https://script.google.com/macros/s/AKfycbzv5hX71jQfvGLK3cHyYv84ECb9rEaR1nwgHMqMkeHQ4ttSXdpzIjYk80xa70RaywpqiQ/exec"
};

export const FIREBASE_CONFIG = {
    // You will need to create a Firebase Project (free) at console.firebase.google.com
    // and paste the configuration object here to enable Auth and Chat without bottlenecks.
    apiKey: "YOUR_API_KEY",
    authDomain: "your-project.firebaseapp.com",
    projectId: "your-project",
    storageBucket: "your-project.appspot.com",
    messagingSenderId: "YOUR_SENDER_ID",
    appId: "YOUR_APP_ID"
};
