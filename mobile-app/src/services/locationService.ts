// src/services/locationService.ts
import * as Location from 'expo-location';
import { Alert } from 'react-native';

export const getCurrentLocation = async () => {
  try {
    // For higher accuracy, you can change this to LocationAccuracy.BestForNavigation
    let location = await Location.getCurrentPositionAsync({
      accuracy: Location.Accuracy.Balanced,
    });
    
    return {
      lat: location.coords.latitude,
      lon: location.coords.longitude,
    };
  } catch (error) {
    console.error('Error getting current location:', error);
    Alert.alert('Location Error', 'Could not fetch current location. Please ensure GPS is enabled.');
    return null;
  }
};