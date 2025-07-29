// ChatComponent.js
import React, { useState, useEffect, useRef } from 'react';
import './ChatComponent.css';
// ConciergeChat.js
import React from 'react';
import ChatComponent from './ChatComponent';

const ConciergeChat = () => {
    const initialMessages = [
        'Welcome to our service! How can I assist you today?',
    ];

    const handleSendMessage = (message) => {
        console.log('User message:', message);
        
    };

    return (
        <ChatComponent
            initialMessages={initialMessages}
            onSendMessage={handleSendMessage}
        />
    );
};

export default ConciergeChat;