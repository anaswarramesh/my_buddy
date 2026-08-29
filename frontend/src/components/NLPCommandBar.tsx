import React, { useState } from 'react';
import { View, TextInput, TouchableOpacity, StyleSheet, Text } from 'react-native';
import { Wand2 } from 'lucide-react-native';
import { THEME } from '../constants/theme';

interface NLPCommandBarProps {
  onExecute: (command: string) => Promise<void>;
}

export const NLPCommandBar: React.FC<NLPCommandBarProps> = ({ onExecute }) => {
  const [command, setCommand] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!command.trim()) return;
    setLoading(true);
    try {
      await onExecute(command);
      setCommand('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <TextInput
        style={styles.input}
        placeholder="e.g. Clear Thursday afternoon & float tasks..."
        placeholderTextColor={THEME.colors.textDim}
        value={command}
        onChangeText={setCommand}
      />
      <TouchableOpacity
        style={[styles.btn, (!command.trim() || loading) && styles.btnDisabled]}
        onPress={handleSubmit}
        disabled={!command.trim() || loading}
      >
        <Wand2 size={16} color="#fff" />
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    gap: 8,
    marginVertical: THEME.spacing.sm,
  },
  input: {
    flex: 1,
    backgroundColor: THEME.colors.cardDark,
    borderRadius: THEME.radius.md,
    borderWidth: 1,
    borderColor: THEME.colors.borderDark,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 12,
    color: THEME.colors.textMain,
  },
  btn: {
    backgroundColor: THEME.colors.amber,
    borderRadius: THEME.radius.md,
    width: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnDisabled: {
    opacity: 0.5,
  }
});
