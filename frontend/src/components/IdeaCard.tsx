import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Target, Award } from 'lucide-react-native';
import { THEME } from '../constants/theme';
import { Idea } from '../types';

interface IdeaCardProps {
  idea: Idea;
}

export const IdeaCard: React.FC<IdeaCardProps> = ({ idea }) => {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{idea.category.toUpperCase()}</Text>
        </View>
        <Text style={styles.date}>{new Date(idea.created_at).toLocaleDateString()}</Text>
      </View>

      <Text style={styles.title}>{idea.title}</Text>
      <Text style={styles.summary}>{idea.summary || idea.raw_transcript}</Text>

      {/* Scores Grid */}
      <View style={styles.scoreRow}>
        <View style={styles.scoreBox}>
          <Text style={styles.scoreLabel}>FEASIBILITY</Text>
          <Text style={[styles.scoreValue, { color: THEME.colors.green }]}>{idea.feasibility_score}%</Text>
        </View>
        <View style={styles.scoreBox}>
          <Text style={styles.scoreLabel}>IMPACT</Text>
          <Text style={[styles.scoreValue, { color: THEME.colors.primaryLight }]}>{idea.impact_score}%</Text>
        </View>
        <View style={styles.scoreBox}>
          <Text style={styles.scoreLabel}>FRICTION</Text>
          <Text style={[styles.scoreValue, { color: THEME.colors.amber }]}>{idea.friction_score}%</Text>
        </View>
      </View>

      {/* Coaching Verdict */}
      {idea.coaching_verdict ? (
        <View style={styles.verdictBox}>
          <Text style={styles.verdictTitle}>COACHING VERDICT</Text>
          <Text style={styles.verdictText}>{idea.coaching_verdict}</Text>
        </View>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: THEME.colors.cardDark,
    borderRadius: THEME.radius.lg,
    borderWidth: 1,
    borderColor: THEME.colors.borderDark,
    padding: THEME.spacing.md,
    marginBottom: THEME.spacing.md,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: THEME.spacing.xs,
  },
  badge: {
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: THEME.radius.sm,
  },
  badgeText: {
    fontSize: 9,
    fontWeight: '700',
    color: THEME.colors.textMuted,
  },
  date: {
    fontSize: 10,
    color: THEME.colors.textDim,
  },
  title: {
    fontSize: 15,
    fontWeight: '700',
    color: THEME.colors.textMain,
    marginTop: 4,
  },
  summary: {
    fontSize: 12,
    color: THEME.colors.textMuted,
    marginTop: 4,
    lineHeight: 16,
  },
  scoreRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: THEME.spacing.md,
  },
  scoreBox: {
    flex: 1,
    backgroundColor: THEME.colors.bgDark,
    borderRadius: THEME.radius.sm,
    padding: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: THEME.colors.borderDark,
  },
  scoreLabel: {
    fontSize: 8,
    fontWeight: '700',
    color: THEME.colors.textDim,
  },
  scoreValue: {
    fontSize: 16,
    fontWeight: '800',
    marginTop: 2,
  },
  verdictBox: {
    marginTop: THEME.spacing.md,
    backgroundColor: THEME.colors.bgDark,
    padding: 10,
    borderRadius: THEME.radius.sm,
    borderLeftWidth: 3,
    borderLeftColor: THEME.colors.primary,
  },
  verdictTitle: {
    fontSize: 9,
    fontWeight: '700',
    color: THEME.colors.primaryLight,
    marginBottom: 2,
  },
  verdictText: {
    fontSize: 11,
    color: THEME.colors.textMain,
    lineHeight: 15,
  }
});
