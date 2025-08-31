// src/screens/LoginScreen.tsx
import React, { useState } from 'react';
import { View, Text, TextInput, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { loginUser } from '../api/chimeraApi';
import { LoginScreenProps } from '../types/navigation';
import { useAuth } from '../context/AuthContext'; // VERIFY THIS IMPORT PATH IS CORRECT

export const LoginScreen = ({ navigation }: LoginScreenProps) => {
  const { signIn } = useAuth(); // THIS LINE SHOULD NOW WORK
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please enter both email and password.');
      return;
    }
    try {
      const response = await loginUser(email, password);
      const { access_token } = response.data;
      await signIn(access_token);
    } catch (error) {
      console.error(error);
      Alert.alert('Login Failed', 'Invalid email or password.');
    }
  };
  
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Welcome Back</Text>
      <TextInput
        style={styles.input}
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      <TouchableOpacity style={styles.button} onPress={handleLogin}>
        <Text style={styles.buttonText}>Login</Text>
      </TouchableOpacity>
      <TouchableOpacity onPress={() => navigation.navigate('Register')}>
        <Text style={styles.switchText}>Don't have an account? Register</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
    container: { flex: 1, justifyContent: 'center', padding: 20, backgroundColor: '#f8fafc' },
    title: { fontSize: 32, fontWeight: 'bold', marginBottom: 40, textAlign: 'center' },
    input: { height: 50, borderColor: '#e2e8f0', borderWidth: 1, borderRadius: 8, paddingHorizontal: 15, marginBottom: 15, backgroundColor: '#ffffff' },
    button: { backgroundColor: '#2563eb', padding: 15, borderRadius: 8, alignItems: 'center', marginTop: 10 },
    buttonText: { color: '#ffffff', fontWeight: 'bold', fontSize: 16 },
    switchText: { marginTop: 20, color: '#2563eb', textAlign: 'center' },
});