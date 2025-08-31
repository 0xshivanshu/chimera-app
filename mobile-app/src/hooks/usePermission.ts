// src/hooks/usePermissions.ts
import { useState, useEffect } from 'react';
import { Platform, Alert } from 'react-native';
import * as Location from 'expo-location';

// We need a separate library for SMS permissions on newer Android versions
// For now, we will focus on Location, as it's directly supported by Expo.
// We will tackle SMS permissions in the next step.

export const usePermissions = () => {
  const [locationGranted, setLocationGranted] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const requestPermissions = async () => {
      if (Platform.OS !== 'android') {
        // Assume non-android platforms are granted for this project
        setLocationGranted(true);
        setIsLoading(false);
        return;
      }

      // Request Location Permission
      const { status: locationStatus } = await Location.requestForegroundPermissionsAsync();
      if (locationStatus !== 'granted') {
        Alert.alert(
          'Permission Required',
          'This app needs access to your location to function properly.',
          [{ text: 'OK' }]
        );
        setLocationGranted(false);
      } else {
        setLocationGranted(true);
      }
      
      // We will add SMS permission logic here in the next step.

      setIsLoading(false);
    };

    requestPermissions();
  }, []);

  return { locationGranted, isLoading };
};