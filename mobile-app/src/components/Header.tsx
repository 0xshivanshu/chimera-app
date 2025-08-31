// src/components/Header.tsx
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Bell, Menu } from 'lucide-react-native';

export const Header = () => {
  return (
    <View style={styles.header}>
      <View style={styles.leftContainer}>
        <TouchableOpacity style={styles.iconButton}>
          <Menu color="#ffffff" size={24} />
        </TouchableOpacity>
        <View>
          <Text style={styles.greetingText}>Good morning</Text>
          <Text style={styles.nameText}>Shivanshu Shekhar</Text>
        </View>
      </View>
      <TouchableOpacity style={styles.iconButton}>
        <Bell color="#ffffff" size={24} />
        <View style={styles.notificationBadge} />
      </TouchableOpacity>
    </View>
  );
};

// We are translating your CSS into a StyleSheet object
const styles = StyleSheet.create({
  header: {
    flexDirection: 'row', // equivalent to 'flex' in CSS
    alignItems: 'center', // equivalent to 'items-center'
    justifyContent: 'space-between', // equivalent to 'justify-between'
    padding: 16, // p-4 in Tailwind (4 * 4px = 16px)
    backgroundColor: '#2563eb', // --primary color
  },
  leftContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12, // equivalent to 'gap-3'
  },
  iconButton: {
    // We use TouchableOpacity for pressable areas
    padding: 8, // To make the touch area larger
  },
  greetingText: {
    color: '#ffffff',
    opacity: 0.8,
  },
  nameText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold', // h2 equivalent
  },
  notificationBadge: {
    position: 'absolute',
    top: 5,
    right: 5,
    width: 12, // w-3
    height: 12, // h-3
    backgroundColor: '#dc2626', // --destructive color (red-500)
    borderRadius: 6, // To make it a circle
  },
});