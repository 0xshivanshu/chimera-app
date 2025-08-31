// src/context/AuthContext.tsx
import React, { createContext, useState, useEffect, useContext, ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';

// 1. VERIFY THIS INTERFACE IS CORRECT
interface AuthContextData {
  userToken: string | null;
  isLoading: boolean;
  signIn: (token: string) => Promise<void>;
  signOut: () => Promise<void>;
}

// Create the context with a default value
const AuthContext = createContext<AuthContextData>({} as AuthContextData);

// Define the type for the component's children
interface AuthProviderProps {
    children: ReactNode;
}

// Create the Provider component
export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [userToken, setUserToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const bootstrapAsync = async () => {
      let token: string | null = null;
      try {
        token = await SecureStore.getItemAsync('userToken');
      } catch (e) {
        console.error('Restoring token failed', e);
      }
      setUserToken(token);
      setIsLoading(false);
    };

    bootstrapAsync();
  }, []);

  // 2. VERIFY THIS OBJECT IS CORRECT
  const authContextValue: AuthContextData = {
    signIn: async (token: string) => {
      await SecureStore.setItemAsync('userToken', token);
      setUserToken(token);
    },
    signOut: async () => {
      await SecureStore.deleteItemAsync('userToken');
      setUserToken(null);
    },
    userToken,
    isLoading,
  };

  return (
    <AuthContext.Provider value={authContextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// 3. VERIFY THIS HOOK IS CORRECT
export const useAuth = () => {
  return useContext(AuthContext);
};