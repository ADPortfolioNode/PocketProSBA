import React, { createContext, useContext, useState } from 'react';

// Create a Context for the app
const AppContext = createContext();

// Create a provider component
export const AppProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  return (
    <AppContext.Provider value={{ user, setUser, loading, setLoading }}>
      {children}
    </AppContext.Provider>
  );
};

// Custom hook to use the AppContext
export const useAppContext = () => {
  return useContext(AppContext);
};
