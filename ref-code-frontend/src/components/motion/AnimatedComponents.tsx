'use client';

import { motion, useMotionValue, useTransform, animate, useInView } from 'motion/react';
import { useEffect, useRef, ReactNode } from 'react';

// ─── Animated Counter ────────────────────────────────────────────────
// Smoothly counts up from 0 to a target value
interface AnimatedCounterProps {
  value: number;
  duration?: number;
  className?: string;
  style?: React.CSSProperties;
}

export function AnimatedCounter({ value, duration = 1, className, style }: AnimatedCounterProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const motionValue = useMotionValue(0);
  const rounded = useTransform(motionValue, (latest) => Math.round(latest));
  const isInView = useInView(ref, { once: true });

  useEffect(() => {
    if (isInView) {
      const controls = animate(motionValue, value, { duration });
      return controls.stop;
    }
  }, [isInView, value, motionValue, duration]);

  useEffect(() => {
    const unsubscribe = rounded.on('change', (latest) => {
      if (ref.current) {
        ref.current.textContent = String(latest);
      }
    });
    return unsubscribe;
  }, [rounded]);

  return <span ref={ref} className={className} style={style}>0</span>;
}

// ─── Fade In ─────────────────────────────────────────────────────────
// Fades in children with optional direction
interface FadeInProps {
  children: ReactNode;
  direction?: 'up' | 'down' | 'left' | 'right' | 'none';
  delay?: number;
  duration?: number;
  className?: string;
}

export function FadeIn({ children, direction = 'up', delay = 0, duration = 0.5, className }: FadeInProps) {
  const directionMap = {
    up: { y: 24, x: 0 },
    down: { y: -24, x: 0 },
    left: { x: 24, y: 0 },
    right: { x: -24, y: 0 },
    none: { x: 0, y: 0 },
  };

  const { x, y } = directionMap[direction];

  return (
    <motion.div
      initial={{ opacity: 0, x, y }}
      animate={{ opacity: 1, x: 0, y: 0 }}
      transition={{ duration, delay, ease: 'easeOut' }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// ─── Fade In When Visible ────────────────────────────────────────────
// Only animates when scrolled into view
interface FadeInViewProps {
  children: ReactNode;
  direction?: 'up' | 'down' | 'left' | 'right' | 'none';
  delay?: number;
  duration?: number;
  className?: string;
}

export function FadeInView({ children, direction = 'up', delay = 0, duration = 0.5, className }: FadeInViewProps) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  const directionMap = {
    up: { y: 30, x: 0 },
    down: { y: -30, x: 0 },
    left: { x: 30, y: 0 },
    right: { x: -30, y: 0 },
    none: { x: 0, y: 0 },
  };

  const { x, y } = directionMap[direction];

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, x, y }}
      animate={isInView ? { opacity: 1, x: 0, y: 0 } : { opacity: 0, x, y }}
      transition={{ duration, delay, ease: 'easeOut' }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// ─── Stagger Children ────────────────────────────────────────────────
// Staggers the animation of child elements
interface StaggerChildrenProps {
  children: ReactNode;
  staggerDelay?: number;
  className?: string;
}

export function StaggerChildren({ children, staggerDelay = 0.1, className }: StaggerChildrenProps) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        hidden: {},
        visible: {
          transition: {
            staggerChildren: staggerDelay,
          },
        },
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// ─── Stagger Item ────────────────────────────────────────────────────
// Individual item within StaggerChildren
interface StaggerItemProps {
  children: ReactNode;
  className?: string;
}

export function StaggerItem({ children, className }: StaggerItemProps) {
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' } },
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// ─── Hover Scale Card ────────────────────────────────────────────────
// Card that scales up slightly on hover with a subtle shadow lift
interface HoverCardProps {
  children: ReactNode;
  className?: string;
  scale?: number;
}

export function HoverCard({ children, className, scale = 1.02 }: HoverCardProps) {
  return (
    <motion.div
      whileHover={{ scale, boxShadow: '0 10px 40px rgba(0,0,0,0.12)' }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// ─── Animated Table Row ──────────────────────────────────────────────
// Table row that fades in with stagger support
interface AnimatedRowProps {
  children: ReactNode;
  index: number;
  className?: string;
}

export function AnimatedRow({ children, index, className }: AnimatedRowProps) {
  return (
    <motion.tr
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05, ease: 'easeOut' }}
      className={className}
    >
      {children}
    </motion.tr>
  );
}

// ─── Pulse Dot ───────────────────────────────────────────────────────
// Animated pulsing status dot
interface PulseDotProps {
  color: string;
  active?: boolean;
  size?: string;
}

export function PulseDot({ color, active = true, size = 'w-2.5 h-2.5' }: PulseDotProps) {
  return (
    <span className="relative inline-flex">
      {active && (
        <motion.span
          className={`absolute inline-flex ${size} rounded-full opacity-75 ${color}`}
          animate={{ scale: [1, 1.8, 1], opacity: [0.75, 0, 0.75] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        />
      )}
      <span className={`relative inline-flex ${size} rounded-full ${color}`} />
    </span>
  );
}

// ─── Shimmer Skeleton ────────────────────────────────────────────────
// Loading skeleton with shimmer effect
interface ShimmerProps {
  className?: string;
}

export function Shimmer({ className = 'h-4 w-full' }: ShimmerProps) {
  return (
    <div className={`relative overflow-hidden rounded bg-gray-200 ${className}`}>
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/60 to-transparent"
        animate={{ x: ['-100%', '100%'] }}
        transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
      />
    </div>
  );
}

// ─── Page Transition Wrapper ─────────────────────────────────────────
interface PageTransitionProps {
  children: ReactNode;
  className?: string;
}

export function PageTransition({ children, className }: PageTransitionProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
