import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  SafeAreaView,
  StatusBar,
  Alert
} from 'react-native';
import { Sparkles, Sun, Clock, BrainCircuit } from 'lucide-react-native';
import { THEME } from '../constants/theme';
import { DailySynthesisResponse } from '../types';
import { CoachPilotAPI } from '../services/api';
import { DensityGauge } from '../components/DensityGauge';
import { VoiceCaptureButton } from '../components/VoiceCaptureButton';
import { StarterTaskCard } from '../components/StarterTaskCard';
import { NLPCommandBar } from '../components/NLPCommandBar';

export const DashboardScreen: React.FC = () => {
  const [data, setData] = useState<DailySynthesisResponse | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const res = await CoachPilotAPI.getDailySynthesis();
      setData(res);
    } catch (e) {
      console.log('Error loading synthesis:', e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleVoiceCapture = async (transcript: string) => {
    try {
      await CoachPilotAPI.processVoiceThought(transcript);
      await loadData();
      Alert.alert('Thought Processed', 'AI evaluated feasibility and generated ignition tasks.');
    } catch (e: any) {
      Alert.alert('Error', e.message);
    }
  };

  const handleAutoSchedule = async (taskId: string) => {
    try {
      await CoachPilotAPI.autoScheduleTask(taskId);
      await loadData();
      Alert.alert('Scheduled!', 'Task successfully placed into lowest-density Green Window.');
    } catch (e: any) {
      Alert.alert('Scheduling Notice', e.message);
    }
  };

  const handleNLPCommand = async (command: string) => {
    try {
      const res = await CoachPilotAPI.executeNLPCommand(command);
      await loadData();
      Alert.alert('Schedule Updated', res.summary_of_changes);
    } catch (e: any) {
      Alert.alert('Error', e.message);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="light-content" />
      <ScrollView
        style={styles.container}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#fff" />}
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.brandRow}>
            <View style={styles.iconBox}>
              <Sparkles size={18} color="#fff" />
            </View>
            <View>
              <Text style={styles.appTitle}>CoachPilot AI</Text>
              <Text style={styles.appSubtitle}>Daily Executive Assistant</Text>
            </View>
          </View>
        </View>

        {/* Morning Synthesis Nudge Banner */}
        <View style={styles.nudgeBanner}>
          <View style={styles.nudgeHeader}>
            <Sun size={14} color={THEME.colors.primaryLight} />
            <Text style={styles.nudgeTag}>DAILY MORNING SYNTHESIS</Text>
          </View>
          <Text style={styles.nudgeText}>
            {data?.coaching_nudge || 'Loading your morning focus plan...'}
          </Text>
        </View>

        {/* Cognitive Density Section */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>TODAY'S COGNITIVE LOAD</Text>
          <View style={styles.densityRow}>
            <DensityGauge
              score={data?.density.score || 0}
              level={data?.density.level || 'light'}
            />
            <View style={styles.densityStats}>
              <View style={styles.statBox}>
                <Text style={styles.statLabel}>Appointments</Text>
                <Text style={styles.statValue}>{data?.density.meeting_count || 0}</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statLabel}>Committed Hours</Text>
                <Text style={styles.statValue}>
                  {data ? (data.density.committed_minutes / 60).toFixed(1) : '0'} hrs
                </Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statLabel}>Focus Windows</Text>
                <Text style={[styles.statValue, { color: THEME.colors.green }]}>
                  {data?.density.available_focus_windows.length || 0} slots
                </Text>
              </View>
            </View>
          </View>
        </View>

        {/* Voice Capture & Ingestion Widget */}
        <VoiceCaptureButton onCapture={handleVoiceCapture} />

        {/* Step 1 Micro-Ignition Task Highlight */}
        {data?.starter_tasks && data.starter_tasks.length > 0 && (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>PRIORITY STARTER ACTIONS</Text>
            {data.starter_tasks.map((task) => (
              <StarterTaskCard
                key={task.id}
                task={task}
                onAutoSchedule={handleAutoSchedule}
              />
            ))}
          </View>
        )}

        {/* Dynamic NLP Rescheduling */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>DYNAMIC NLP RESCHEDULING</Text>
          <Text style={styles.sectionSubtitle}>
            Shift tasks or clear calendar blocks with conversational commands.
          </Text>
          <NLPCommandBar onExecute={handleNLPCommand} />
        </View>

        {/* Today's Agenda */}
        <View style={styles.card}>
          <View style={styles.agendaHeader}>
            <Text style={styles.sectionTitle}>TODAY'S AGENDA</Text>
            <Clock size={14} color={THEME.colors.textDim} />
          </View>
          {data?.today_events.map((ev) => (
            <View
              key={ev.id}
              style={[
                styles.eventItem,
                ev.event_category === 'ai_starter_task' && styles.eventItemTask
              ]}
            >
              <Text style={styles.eventTime}>
                {new Date(ev.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </Text>
              <View style={styles.eventDetails}>
                <Text style={styles.eventTitle}>{ev.title}</Text>
                <Text style={styles.eventCat}>
                  {ev.event_category === 'ai_starter_task' ? '⚡ AI Ignition Block' : 'Appointment'}
                </Text>
              </View>
            </View>
          ))}
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: THEME.colors.bgDark,
  },
  container: {
    flex: 1,
    paddingHorizontal: THEME.spacing.md,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: THEME.spacing.md,
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  iconBox: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: THEME.colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  appTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: THEME.colors.textMain,
  },
  appSubtitle: {
    fontSize: 11,
    color: THEME.colors.textMuted,
  },
  nudgeBanner: {
    backgroundColor: THEME.colors.cardDark,
    borderRadius: THEME.radius.lg,
    borderWidth: 1,
    borderColor: THEME.colors.borderDark,
    padding: THEME.spacing.md,
    marginBottom: THEME.spacing.md,
  },
  nudgeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 6,
  },
  nudgeTag: {
    fontSize: 10,
    fontWeight: '700',
    color: THEME.colors.primaryLight,
    letterSpacing: 0.5,
  },
  nudgeText: {
    fontSize: 13,
    color: THEME.colors.textMain,
    lineHeight: 18,
  },
  card: {
    backgroundColor: THEME.colors.cardDark,
    borderRadius: THEME.radius.lg,
    borderWidth: 1,
    borderColor: THEME.colors.borderDark,
    padding: THEME.spacing.md,
    marginBottom: THEME.spacing.md,
  },
  sectionTitle: {
    fontSize: 10,
    fontWeight: '700',
    color: THEME.colors.textDim,
    letterSpacing: 0.5,
    marginBottom: THEME.spacing.sm,
  },
  sectionSubtitle: {
    fontSize: 11,
    color: THEME.colors.textMuted,
    marginBottom: 8,
  },
  densityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 20,
    marginTop: 4,
  },
  densityStats: {
    flex: 1,
    gap: 8,
  },
  statBox: {
    backgroundColor: THEME.colors.bgDark,
    padding: 8,
    borderRadius: THEME.radius.sm,
    borderWidth: 1,
    borderColor: THEME.colors.borderDark,
  },
  statLabel: {
    fontSize: 9,
    color: THEME.colors.textDim,
    fontWeight: '600',
  },
  statValue: {
    fontSize: 14,
    fontWeight: '700',
    color: THEME.colors.textMain,
    marginTop: 2,
  },
  agendaHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  eventItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: THEME.colors.borderDark,
  },
  eventItemTask: {
    backgroundColor: 'rgba(99, 102, 241, 0.1)',
    borderRadius: THEME.radius.sm,
    paddingHorizontal: 8,
  },
  eventTime: {
    fontSize: 11,
    fontFamily: 'monospace',
    color: THEME.colors.textDim,
  },
  eventDetails: {
    flex: 1,
  },
  eventTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: THEME.colors.textMain,
  },
  eventCat: {
    fontSize: 10,
    color: THEME.colors.textMuted,
  }
});
