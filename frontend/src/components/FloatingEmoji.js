import React, { useEffect } from 'react';

/**
 * Floating emoji animation component
 * Emoji floats from bottom to top and fades out
 */
function FloatingEmoji({ emoji, onComplete }) {
  useEffect(() => {
    // Animation duration
    const duration = 3000; // 3 seconds
    
    // Call onComplete after animation
    const timer = setTimeout(() => {
      if (onComplete) {
        onComplete();
      }
    }, duration);

    return () => clearTimeout(timer);
  }, [onComplete]);

  // Random horizontal offset for variety
  const randomOffset = Math.random() * 100 - 50; // -50px to +50px

  return (
    <div
      className="absolute bottom-20 left-1/2 pointer-events-none animate-float-up"
      style={{
        transform: `translate(calc(-50% + ${randomOffset}px), 0)`,
      }}
    >
      <span className="text-4xl block">{emoji}</span>
    </div>
  );
}

export default FloatingEmoji;

