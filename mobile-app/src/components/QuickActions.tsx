// src/components/QuickActions.tsx
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { ArrowUpRight, ArrowDownLeft, CreditCard, QrCode } from 'lucide-react-native';

interface QuickActionsProps {
  onSendClick: () => void;
}

export const QuickActions = ({ onSendClick }: QuickActionsProps) => {
  const actions = [
    { icon: ArrowUpRight, label: "Send", color: "#e0f2fe", iconColor: "#2563eb", onPress: onSendClick },
    { icon: ArrowDownLeft, label: "Receive", color: "#dcfce7", iconColor: "#16a34a", onPress: () => {} },
    { icon: CreditCard, label: "Pay Bills", color: "#f3e8ff", iconColor: "#9333ea", onPress: () => {} },
    { icon: QrCode, label: "QR Pay", color: "#fff7ed", iconColor: "#f97316", onPress: () => {} },
  ];

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Quick Actions</Text>
      <View style={styles.grid}>
        {actions.map((action, index) => (
          <TouchableOpacity key={index} style={styles.button} onPress={action.onPress}>
            <View style={[styles.iconContainer, { backgroundColor: action.color }]}>
              <action.icon color={action.iconColor} size={28} />
            </View>
            <Text style={styles.label}>{action.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
    color: '#1e293b',
  },
  grid: {
    flexDirection: 'row',
    justifyContent: 'space-around', // Use space-around for better spacing
  },
  button: {
    alignItems: 'center',
    gap: 8,
  },
  iconContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
  },
  label: {
    fontSize: 14,
    color: '#475569',
  },
});