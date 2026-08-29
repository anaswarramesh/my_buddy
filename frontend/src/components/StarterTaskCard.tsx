import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Zap, CalendarPlus, CheckCircle } from 'lucide-react-native';
import { THEME } from '../constants/theme';
import { Task } from '../types';

interface StarterTaskCardProps {
  task: Task;
  onAutoSchedule: (taskId: string) => Promise<void>;
}

export const StarterTaskCard: React.FC<StarterTaskCardProps> = ({ task, onAutoSchedule }) => {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.tag}>
          <Zap size={12} color={THEME.colors.primaryLight} />
          <Text style={styles.tagText}>STEP 1: MICRO-IGNITION (≤15M)</Text>
        </View>
        <Text style={styles.duration}>{task.estimated_minutes} mins</Text>
      </View>

      <Text style={styles.title}>{task.title}</Text>
      {task.description ? <Text style={styles.description}>{task.description}</Text> : null}

      <View style={styles.footer}>
        {task.is_scheduled ? (
          <View style={styles.scheduledStatus}>
            <CheckCircle size={14} color={THEME.colors.green} />
            <Text style={styles.scheduledText}>
              Scheduled: {new Date(task.scheduled_start!).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </Text>
          </View>
        ) : (
          <TouchableOpacity
            style={styles.scheduleBtn}
            onPress={() => onAutoSchedule(task.id)}
          >
            <CalendarPlus size={14} color="#fff" />
            <Text style={styles.scheduleBtnText}>Auto-Schedule in Green Slot</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: 'rgba(99, 102, 241, 0.1)',
    borderRadius: THEME.radius.lg,
    borderWidth: 1,
    borderColor: 'rgba(99, 102, 241, 0.3)',
    padding: THEME.spacing.md,
    marginVertical: THEME.spacing.sm,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: THEME.spacing.xs,
  },
  tag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  tagText: {
    fontSize: 10,
    fontWeight: '700',
    color: THEME.colors.primaryLight,
    letterSpacing: 0.5,
  },
  duration: {
    fontSize: 11,
    color: THEME.colors.textMuted,
  },
  title: {
    fontSize: 14,
    fontWeight: '700',
    color: THEME.colors.textMain,
    marginTop: 4,
  },
  description: {
    fontSize: 12,
    color: THEME.colors.textMuted,
    marginTop: 4,
    lineHeight: 16,
  },
  footer: {
    marginTop: THEME.spacing.md,
    flexDirection: 'row',
    justifyContent: 'flex-end',
  },
  scheduleBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: THEME.colors.green,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: THEME.radius.sm,
  },
  scheduleBtnText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#fff',
  },
  scheduledStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  scheduledText: {
    fontSize: 11,
    fontWeight: '600',
    color: THEME.colors.green,
  }
});
