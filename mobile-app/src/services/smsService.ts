// src/services/smsService.ts
import { PermissionsAndroid, Alert } from 'react-native';
import SmsListener from 'react-native-android-sms-listener';
import { sendAlert } from '../api/chimeraApi'; // Now this import works

// This function requests the SMS permission
export const requestSmsPermission = async (): Promise<boolean> => {
  try {
    const granted = await PermissionsAndroid.request(
      PermissionsAndroid.PERMISSIONS.RECEIVE_SMS,
      {
        title: 'SMS Permission Required',
        message: 'This app needs to read incoming SMS messages to detect phishing attempts.',
        buttonPositive: 'OK',
        buttonNegative: 'Cancel',
      },
    );
    return granted === PermissionsAndroid.RESULTS.GRANTED;
  } catch (err) {
    console.warn(err);
    return false;
  }
};

// This function starts listening for SMS messages
export const startSmsListener = (userId: string) => {
  console.log('Starting SMS listener...');
  
  // TypeScript now understands what addListener and message are, so there are no errors.
  const subscription = SmsListener.addListener(message => {
    console.log('New SMS Received:', message.body);
    
    const payload = {
      alert_type: 'SMS Received',
      user_id: userId,
      event_data: {
        sms_text: message.body,
      },
    };

    sendAlert(payload)
      .then(() => {
        console.log(`Successfully sent SMS alert to backend for user ${userId}.`);
      })
      .catch(error => {
        console.error('Failed to send SMS alert:', error);
      });
  });

  // TypeScript now knows the subscription object has a .remove() method
  return subscription;
};