import { useEffect, useRef } from 'react';

const coats = [
  { fur: '#f3c98a', ear: '#a86944', patch: '#fff4df', collar: '#1d4978' },
  { fur: '#e4ded3', ear: '#867368', patch: '#ffffff', collar: '#c77667' },
  { fur: '#b9a58c', ear: '#5d4b42', patch: '#eadbc9', collar: '#d5a446' },
];

function Puppy({ index }: { index: number }) {
  const color = coats[index];
  return (
    <svg viewBox="0 0 92 98" role="presentation" aria-hidden="true">
      <path d="M66 68 C86 57 91 77 79 83" fill="none" stroke={color.ear} strokeWidth="10" strokeLinecap="round" className="puppy-tail" />
      <ellipse cx="46" cy="75" rx="26" ry="19" fill={color.fur} />
      <ellipse cx="46" cy="78" rx="13" ry="12" fill={color.patch} />
      <ellipse cx="27" cy="89" rx="10" ry="6" fill={color.fur} />
      <ellipse cx="65" cy="89" rx="10" ry="6" fill={color.fur} />
      <path d="M21 21 C1 9 3 51 20 55 L29 35 Z" fill={color.ear} className="puppy-ear puppy-ear-left" />
      <path d="M71 21 C91 9 89 51 72 55 L63 35 Z" fill={color.ear} className="puppy-ear puppy-ear-right" />
      <ellipse cx="46" cy="41" rx="31" ry="30" fill={color.fur} />
      <path d="M27 48 C26 36 35 31 46 36 C57 31 66 36 65 48 C64 60 57 66 46 67 C35 66 28 60 27 48" fill={color.patch} />
      <ellipse cx="34" cy="39" rx="3.2" ry="4.4" fill="#2d2926" />
      <ellipse cx="58" cy="39" rx="3.2" ry="4.4" fill="#2d2926" />
      <circle cx="35" cy="38" r="1" fill="white" />
      <circle cx="59" cy="38" r="1" fill="white" />
      <ellipse cx="46" cy="50" rx="6" ry="4.5" fill="#332b2a" />
      <path d="M46 54 C46 60 39 61 36 56 M46 54 C46 60 53 61 56 56" fill="none" stroke="#6a4b48" strokeWidth="2" strokeLinecap="round" />
      <circle cx="29" cy="49" r="3" fill="#e6a7a1" opacity=".7" />
      <circle cx="63" cy="49" r="3" fill="#e6a7a1" opacity=".7" />
      <path d="M33 67 Q46 75 59 67" fill="none" stroke={color.collar} strokeWidth="6" strokeLinecap="round" />
      <circle cx="46" cy="72" r="3.5" fill="#f4cb65" />
    </svg>
  );
}

export default function PuppyTrail() {
  const container = useRef<HTMLDivElement>(null);
  const pups = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)');
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (!finePointer.matches || reducedMotion.matches) return;

    const target = { x: -120, y: -120 };
    const positions = coats.map(() => ({ x: -120, y: -120 }));
    let frame = 0;

    const move = (event: PointerEvent) => {
      target.x = event.clientX;
      target.y = event.clientY;
      if (container.current) container.current.style.opacity = '1';
    };
    const hide = () => {
      if (container.current) container.current.style.opacity = '0';
    };
    const animate = () => {
      let leadX = target.x + 20;
      let leadY = target.y + 18;
      positions.forEach((position, index) => {
        const easing = 0.24 - index * 0.035;
        position.x += (leadX - position.x) * easing;
        position.y += (leadY - position.y) * easing;
        const pup = pups.current[index];
        if (pup) pup.style.transform = `translate3d(${position.x}px, ${position.y}px, 0)`;
        leadX = position.x - 32;
        leadY = position.y + 18;
      });
      frame = window.requestAnimationFrame(animate);
    };

    window.addEventListener('pointermove', move, { passive: true });
    document.addEventListener('mouseleave', hide);
    frame = window.requestAnimationFrame(animate);
    return () => {
      window.removeEventListener('pointermove', move);
      document.removeEventListener('mouseleave', hide);
      window.cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <div className="puppy-trail" ref={container} aria-hidden="true">
      {coats.map((_, index) => (
        <div
          className={`puppy-follower puppy-follower-${index + 1}`}
          data-puppy={index + 1}
          key={index}
          ref={(element) => { pups.current[index] = element; }}
        >
          <Puppy index={index} />
        </div>
      ))}
    </div>
  );
}
