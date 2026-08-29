import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Circle } from 'react-native-svg';
import { THEME } from '../constants/theme';
import { DensityLevel } from '../types';

interface DensityGaugeProps {
  score: number; // 0.0 to 1.0
  level: DensityLevel;
}

export const DensityGauge: React.FC<DensityGaugeProps> = ({ score, level }) => {
  const size = 120;
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score * circumference);

  const getTierColor = () => {
    switch (level) {
      case 'light': return THEME.colors.green;
      case 'moderate': return THEME.colors.amber;
      default: return THEME.colors.rose;
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.svgWrapper}>
        <Svg width={size} height={size}>
          <Circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={THEME.colors.borderDark}
            strokeWidth={strokeWidth}
            fill="none"
          />
          <Circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={getTierColor()}
            strokeWidth={strokeWidth}
            strokeDasharray={`${circumference} ${circumference}`}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="none"
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
          />
        </Svg>
        <View style={styles.labelContainer}>
          <Text style={styles.scoreText}>{Math.round(score * 100)}%</Text>
          <Text style={styles.loadText}>LOAD</Text>
        </View>
      </View>
      <View style={[styles.badge, { backgroundColor: getTierColor() + '20', borderColor: getTierColor() + '40' }]}>
        <Text style={[styles.badgeText, { color: getTierColor() }]}>{level.toUpperCase()}</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  svgWrapper: {
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  labelContainer: {
    position: 'absolute',
    alignItems: 'center',
  },
  scoreText: {
    fontSize: 22,
    fontWeight: '800',
    color: THEME.colors.textMain,
  },
  loadText: {
    fontSize: 9,
    fontWeight: '600',
    color: THEME.colors.textMuted,
    letterSpacing: 1,
  },
  badge: {
    marginTop: 8,
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: THEME.radius.full,
    borderWidth: 1,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  }
});
