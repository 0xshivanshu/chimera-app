// src/types/sms-listener.d.ts

declare module 'react-native-android-sms-listener' {
  interface SmsMessage {
    originatingAddress: string;
    body: string;
    timestamp: number;
  }

  interface SmsSubscription {
    remove: () => void;
  }

  const SmsListener: {
    addListener: (callback: (message: SmsMessage) => void) => SmsSubscription;
  };

  export default SmsListener;
}