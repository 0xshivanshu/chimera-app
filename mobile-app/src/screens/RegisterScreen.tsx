// src/screens/RegisterScreen.tsx
import React, { useState } from 'react';
import { View, Text, TextInput, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { registerUser } from '../api/chimeraApi';
import { RegisterScreenProps } from '../types/navigation'; // <-- IMPORT THE TYPE

// We apply the imported 'RegisterScreenProps' type here
export const RegisterScreen = ({ navigation }: RegisterScreenProps) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleRegister = async () => {
    if (!email || !password) {
        Alert.alert('Error', 'Please fill in all fields.');
        return;
    }
    try {
        await registerUser(email, password);
        Alert.alert('Success', 'Registration successful! Please log in.');
        navigation.navigate('Login');
    } catch (error) {
        console.error(error);
        Alert.alert('Registration Failed', 'This email may already be in use.');
    }
  };

  // ... (the rest of the component's JSX and styles remain exactly the same)
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Create Account</Text>
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
      <TouchableOpacity style={styles.button} onPress={handleRegister}>
        <Text style={styles.buttonText}>Register</Text>
      </TouchableOpacity>
      <TouchableOpacity onPress={() => navigation.navigate('Login')}>
        <Text style={styles.switchText}>Already have an account? Login</Text>
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