// src/components/BottomNavigation.tsx
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Home, CreditCard, PieChart, User } from 'lucide-react-native';
import type { LucideIcon } from 'lucide-react-native';

interface NavItem {
  icon: LucideIcon;
  label: string;
  active: boolean;
}

const navItems: NavItem[] = [
  { icon: Home, label: "Home", active: true },
  { icon: CreditCard, label: "Cards", active: false },
  { icon: PieChart, label: "Analytics", active: false },
  { icon: User, label: "Profile", active: false },
];

export const BottomNavigation = () => {
  return (
    <View style={styles.navContainer}>
      {navItems.map((item, index) => (
        <TouchableOpacity key={index} style={[styles.navButton, item.active && styles.activeButton]}>
          <item.icon color={item.active ? '#2563eb' : '#64748b'} size={24} />
          <Text style={[styles.navLabel, item.active && styles.activeLabel]}>
            {item.label}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  navContainer: {
    flexDirection: 'row',
    height: 70,
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
  },
  navButton: {
    flex: 1, // Each button takes up equal space
    justifyContent: 'center',
    alignItems: 'center',
    gap: 4,
  },
  activeButton: {
    backgroundColor: 'rgba(37, 99, 235, 0.05)', // bg-primary/5
  },
  navLabel: {
    fontSize: 12,
    color: '#64748b', // muted-foreground
  },
  activeLabel: {
    color: '#2563eb', // primary
  },
});