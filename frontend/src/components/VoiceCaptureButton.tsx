import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { Mic, Zap } from 'lucide-react-native';
import { THEME } from '../constants/theme';

interface VoiceCaptureButtonProps {
  onCapture: (transcript: string) => Promise<void>;
}

export const VoiceCaptureButton: React.FC<VoiceCaptureButtonProps> = ({ onCapture }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleToggle = async () => {
    if (!isRecording) {
      setIsRecording(true);
    } else {
      setIsRecording(false);
      setIsProcessing(true);
      try {
        // Capture & process thought
        await onCapture("I want to build an automated AI client intake system that summarizes legal inquiries.");
      } finally {
        setIsProcessing(false);
      }
    }
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity
        onPress={handleToggle}
        disabled={isProcessing}
        style={[
          styles.button,
          isRecording && styles.buttonRecording,
          isProcessing && styles.buttonProcessing
        ]}
      >
        {isProcessing ? (
          <ActivityIndicator color="#fff" size="small" />
        ) : (
          <Mic color="#fff" size={28} />
        )}
      </TouchableOpacity>
      <Text style={[styles.statusText, isRecording && styles.statusRecording]}>
        {isProcessing
          ? "Whisper transcribing & Prompt A coaching..."
          : isRecording
          ? "Listening... Tap to submit thought"
          : "Press to capture thought / idea"}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    marginVertical: THEME.spacing.md,
  },
  button: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: '#2563eb', // blue-600
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#2563eb',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.4,
    shadowRadius: 12,
    elevation: 8,
  },
  buttonRecording: {
    backgroundColor: THEME.colors.rose,
    shadowColor: THEME.colors.rose,
  },
  buttonProcessing: {
    backgroundColor: THEME.colors.primary,
  },
  statusText: {
    marginTop: 10,
    fontSize: 12,
    fontWeight: '600',
    color: THEME.colors.textMuted,
  },
  statusRecording: {
    color: THEME.colors.rose,
  }
});
