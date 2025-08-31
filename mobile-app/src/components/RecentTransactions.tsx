// src/components/RecentTransactions.tsx
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, FlatList } from 'react-native';
import { ChevronRight } from 'lucide-react-native';

// --- TYPE DEFINITION START ---
// Define the shape of a single transaction object
type Transaction = {
  id: string;
  type: string;
  date: string;
  amount: string;
  color: string;
  iconColor: string;
};
// --- TYPE DEFINITION END ---


// Use our new Transaction type for the static data array
const transactions: Transaction[] = [
  {
    id: '1',
    type: "Coffee Shop",
    date: "Today",
    amount: "-₹45.00",
    color: "#fee2e2",
    iconColor: "#dc2626",
  },
  {
    id: '2',
    type: "Salary Deposit",
    date: "Yesterday",
    amount: "+₹3,200.00",
    color: "#dcfce7",
    iconColor: "#16a34a",
  },
  {
    id: '3',
    type: "Online Shopping",
    date: "August 25",
    amount: "-₹1,250.00",
    color: "#fee2e2",
    iconColor: "#dc2626",
  },
];

// Apply the type to the component's props
const TransactionItem = ({ item }: { item: Transaction }) => (
  <TouchableOpacity style={styles.card}>
    <View style={styles.leftContent}>
      <View style={[styles.iconContainer, { backgroundColor: item.color }]}>
      </View>
      <View>
        <Text style={styles.typeText}>{item.type}</Text>
        <Text style={styles.dateText}>{item.date}</Text>
      </View>
    </View>
    <View style={styles.rightContent}>
      <Text style={[styles.amountText, { color: item.amount.startsWith('+') ? '#16a34a' : '#dc2626' }]}>
        {item.amount}
      </Text>
    </View>
  </TouchableOpacity>
);

export const RecentTransactions = () => {
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Recent Transactions</Text>
        <TouchableOpacity style={styles.viewAllButton}>
          <Text style={styles.viewAllText}>View All</Text>
          <ChevronRight color="#2563eb" size={16} />
        </TouchableOpacity>
      </View>
      
      <FlatList
        data={transactions}
        renderItem={({ item }) => <TransactionItem item={item} />}
        keyExtractor={item => item.id}
        scrollEnabled={false}
        ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: { padding: 16 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  title: { fontSize: 20, fontWeight: 'bold', color: '#1e293b' },
  viewAllButton: { flexDirection: 'row', alignItems: 'center' },
  viewAllText: { color: '#2563eb', marginRight: 4 },
  card: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#ffffff', padding: 16, borderRadius: 12, borderWidth: 1, borderColor: '#e2e8f0' },
  leftContent: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  iconContainer: { width: 40, height: 40, borderRadius: 20, justifyContent: 'center', alignItems: 'center' },
  typeText: { fontWeight: '500', color: '#1e293b' },
  dateText: { fontSize: 12, color: '#64748b' },
  rightContent: { alignItems: 'flex-end' },
  amountText: { fontWeight: 'bold' },
});