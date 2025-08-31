// src/screens/HomeScreen.tsx (Final Layout)
import React from 'react';
import { View, StyleSheet, SafeAreaView, StatusBar, Platform, ScrollView, Text } from 'react-native';
import { useAuth } from '../context/AuthContext';
import { usePermissions } from '../hooks/usePermission';
import { getCurrentLocation } from '../services/locationService'; // <-- IMPORT
import { onboardLocation } from '../api/chimeraApi';
import { Header } from '../components/Header';
import { AccountBalance } from '../components/AccountBalance';
import { QuickActions } from '../components/QuickActions';
import { RecentTransactions } from '../components/RecentTransactions';
import { BottomNavigation } from '../components/BottomNavigation'; // <-- IMPORT
import { useState, useEffect } from 'react';
import { AxiosError } from 'axios';
export const HomeScreen = () => {
  const { userToken } = useAuth(); // Get user token to decode for user ID
  const { locationGranted, isLoading: permissionsLoading } = usePermissions();

  useEffect(() => {
    const handleOnboarding = async () => {
      if (locationGranted && userToken) {
        console.log("Location permission is granted. Fetching coordinates...");
        
        // 1. Get current location from the device
        const location = await getCurrentLocation();
        
        if (location) {
          console.log(`Location fetched: Lat ${location.lat}, Lon ${location.lon}`);
          
          try {
            // HACK: For now, we'll use the first part of the token as a pseudo user ID.
            // In a real app, you would decode the JWT to get the user's email/ID.
            const pseudoUserId = userToken.split('.')[1]; 

            // 2. Send location data to the backend
            await onboardLocation(pseudoUserId, location.lat, location.lon);
            console.log("Successfully onboarded user's location to the backend.");
            
          } catch (error) {
            if (error instanceof AxiosError) {
              // Now TypeScript knows 'error' is an AxiosError
              console.error("Failed to onboard location:", error.response?.data || error.message);
            } else {
              // Handle other types of errors
              console.error("An unexpected error occurred:", error);
            }
          }
        }
      } else if (!permissionsLoading && !locationGranted) {
        console.log("Location permission was denied. Cannot onboard location.");
      }
    };

    handleOnboarding();
    
  }, [permissionsLoading, locationGranted, userToken]);

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" backgroundColor="#2563eb" />
      <View style={styles.container}>
        <Header />
        <ScrollView style={styles.scrollView}>
          {permissionsLoading && <Text style={styles.loadingText}>Checking permissions...</Text>}          <AccountBalance />
          <QuickActions onSendClick={() => console.log('Send money clicked!')} />
          <RecentTransactions />
        </ScrollView>
        <BottomNavigation />
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
    loadingText: {
    textAlign: 'center',
    padding: 10,
    color: '#64748b',
  },
  safeArea: {
    flex: 1,
    backgroundColor: '#f8fafc',
    paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0,
  },
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1, // This makes the ScrollView take up the available space
  },
});