// src/components/AccountBalance.tsx
import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Eye, EyeOff } from 'lucide-react-native';
import { LinearGradient } from 'expo-linear-gradient';

export const AccountBalance = () => {
  const [showBalance, setShowBalance] = useState(true);

  return (
    <View style={styles.outerContainer}>
      <LinearGradient
        colors={['#2563eb', '#1d4ed8']} // Gradient from blue-600 to blue-700
        style={styles.card}
      >
        <View style={styles.topRow}>
          <Text style={styles.labelText}>Total Balance</Text>
          <TouchableOpacity onPress={() => setShowBalance(!showBalance)}>
            {showBalance ? (
              <EyeOff color="white" size={20} />
            ) : (
              <Eye color="white" size={20} />
            )}
          </TouchableOpacity>
        </View>

        <Text style={styles.balanceText}>
          {showBalance ? '₹12,486.50' : '••••••'}
        </Text>
        
        <View style={styles.bottomRow}>
          <View>
            <Text style={styles.labelText}>Available</Text>
            <Text style={styles.subBalanceText}>
              {showBalance ? '₹11,950.00' : '••••••'}
            </Text>
          </View>
          <View style={{ alignItems: 'flex-end' }}>
            <Text style={styles.labelText}>Savings</Text>
            <Text style={styles.subBalanceText}>
              {showBalance ? '₹536.50' : '••••••'}
            </Text>
          </View>
        </View>
      </LinearGradient>
    </View>
  );
};

const styles = StyleSheet.create({
  outerContainer: {
    marginHorizontal: 16,
    marginTop: 16,
  },
  card: {
    padding: 24,
    borderRadius: 12,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  labelText: {
    color: 'white',
    opacity: 0.8,
  },
  balanceText: {
    color: 'white',
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  bottomRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  subBalanceText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '500',
  },
});