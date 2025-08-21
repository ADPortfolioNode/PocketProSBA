import React, { createContext, useContext, useState } from 'react';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [globalState, setGlobalState] = useState({});

  const updateGlobalState = (key, value) => {
    setGlobalState(prevState => ({
      ...prevState,
      [key]: value
    }));
  };

  return (
    <AppContext.Provider value={{ globalState, updateGlobalState }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  return useContext(AppContext);
};