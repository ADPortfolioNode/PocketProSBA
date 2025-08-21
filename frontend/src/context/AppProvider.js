import React, { createContext, useContext, useState } from 'react';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  // Add other global states as needed

  const value = {
    user,
    setUser,
    chatMessages,
    setChatMessages,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useAppContext = () => {
  return useContext(AppContext);
};
