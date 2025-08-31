// src/types/navigation.ts
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

// This defines all the screens available in your app's navigation stack
export type RootStackParamList = {
  Login: undefined;
  Register: undefined;
  Home: undefined;
};

// This creates a specific type for the props of the Login screen
export type LoginScreenProps = NativeStackScreenProps<RootStackParamList, 'Login'>;

// This creates a specific type for the props of the Register screen
export type RegisterScreenProps = NativeStackScreenProps<RootStackParamList, 'Register'>;

// We can add types for other screens here as we create them