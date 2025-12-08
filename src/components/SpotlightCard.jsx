import { useRef, useState } from 'react';

const SpotlightCard = ({ children, className = '', spotlightColor = 'rgba(255, 255, 255, 0.25)' }) => {
  const divRef = useRef(null);
  const [isFocused, setIsFocused] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [opacity, setOpacity] = useState(0);

  const handleMouseMove = e => {
    if (!divRef.current || isFocused) return;

    const rect = divRef.current.getBoundingClientRect();
    setPosition({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  const handleFocus = () => {
    setIsFocused(true);
    setOpacity(0.6);
  };

  const handleBlur = () => {
    setIsFocused(false);
    setOpacity(0);
  };

  const handleMouseEnter = () => {
    setOpacity(0.6);
  };

  const handleMouseLeave = () => {
    setOpacity(0);
  };

  const handleTouchStart = e => {
    setOpacity(0.6);
    if (!divRef.current) return;
    const rect = divRef.current.getBoundingClientRect();
    const t = e.touches[0];
    setPosition({ x: t.clientX - rect.left, y: t.clientY - rect.top });
  };

  const handleTouchMove = e => {
    if (!divRef.current) return;
    const rect = divRef.current.getBoundingClientRect();
    const t = e.touches[0];
    setPosition({ x: t.clientX - rect.left, y: t.clientY - rect.top });
  };

  const handleTouchEnd = () => {
    setOpacity(0);
  };

  return (
    <div
      ref={divRef}
      tabIndex={0}
      onMouseMove={handleMouseMove}
      onFocus={handleFocus}
      onBlur={handleBlur}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      className={`relative rounded-3xl border border-white/10 bg-[#271E37]/60 backdrop-blur-xl overflow-hidden p-8 ${className}`}>
      <div
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-500 ease-in-out"
        style={{
          opacity,
          background: `radial-gradient(circle at ${position.x}px ${position.y}px, ${spotlightColor}, transparent 80%)`
        }} />
      {children}
    </div>
  );
};

export default SpotlightCard;
