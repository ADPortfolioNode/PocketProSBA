import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

// Hero video slideshow: one video slot in the home hero, one workflow per
// slide, so each workflow's prep video is modular — add, remove, or reorder
// a slide by editing SLIDES only, without touching the hero layout.
//
// Sound behaviour, by design: the active slide plays muted on a loop until
// the user clicks it (or the sound button). Browsers only allow autoplay
// with sound after a user gesture, and a hero that talks uninvited is a
// distraction — silent until clicked is the point. The slide does NOT
// auto-advance: a rotating hero would pull attention while the user reads
// the hero copy next to it.
const SLIDES = [
  {
    title: 'Programs',
    blurb: 'See SBA programs at a glance before you ask about any of them.',
    video: '/demo-videos/programs.mp4',
    to: '/sba',
    tryLabel: 'Try Programs',
  },
  {
    title: 'Browse resources',
    blurb: 'Find live SBA guides and official resources, kept current.',
    video: '/demo-videos/browse.mp4',
    to: '/browse',
    tryLabel: 'Try Browse',
  },
  {
    title: 'Chat concierge',
    blurb: 'Ask in plain language and get guidance plus next steps.',
    video: '/demo-videos/chat.mp4',
    to: '/chat',
    tryLabel: 'Try Chat',
  },
  {
    title: 'RAG retrieval',
    blurb: 'See how answers are pulled from the knowledge base.',
    video: '/demo-videos/rag.mp4',
    to: '/rag',
    tryLabel: 'Try Knowledge RAG',
  },
  {
    title: 'Task orchestrator',
    blurb: 'Watch a complex funding question break into guided steps.',
    video: '/demo-videos/orchestrator.mp4',
    to: '/orchestrator',
    tryLabel: 'Try Task workflows',
  },
  {
    title: 'Documents',
    blurb: 'Upload and manage the documents a lender will ask for.',
    video: '/demo-videos/documents.mp4',
    to: '/documents',
    tryLabel: 'Try Documents',
  },
];

function HeroWorkflowShowcase() {
  const [index, setIndex] = useState(0);
  const [soundOn, setSoundOn] = useState(false);
  const videoRef = useRef(null);
  const slide = SLIDES[index];

  // Play the active slide's video (muted until the user opts into sound).
  // jsdom and some browsers reject play() without a gesture; never let that
  // break the hero.
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    video.muted = !soundOn;
    try {
      const result = video.play();
      if (result && typeof result.catch === 'function') result.catch(() => {});
    } catch (err) {
      // Playing is a progressive enhancement; the poster frame still shows.
    }
  }, [index, soundOn]);

  const prev = () => setIndex((i) => (i - 1 + SLIDES.length) % SLIDES.length);
  const next = () => setIndex((i) => (i + 1) % SLIDES.length);

  return (
    <div className="svc-hero-showcase" aria-label="Workflow videos">
      <div className="svc-hero-showcase-media">
        <video
          key={slide.video}
          ref={videoRef}
          src={slide.video}
          muted={!soundOn}
          loop
          playsInline
          preload="metadata"
          className="svc-hero-video"
          onClick={() => setSoundOn((v) => !v)}
          aria-label={`${slide.title} workflow video. Click to ${soundOn ? 'mute' : 'turn sound on'}.`}
        />
        <button
          type="button"
          className="svc-hero-sound"
          onClick={() => setSoundOn((v) => !v)}
          aria-label={soundOn ? 'Mute video' : 'Turn video sound on'}
        >
          {soundOn ? '🔊 Sound on' : '🔇 Click video for sound'}
        </button>
      </div>
      <div className="svc-hero-showcase-caption">
        <h2>{slide.title}</h2>
        <p>{slide.blurb}</p>
        <Link to={slide.to} className="pp-btn pp-btn-primary">
          {slide.tryLabel} →
        </Link>
      </div>
      <div className="svc-hero-showcase-controls">
        <button type="button" onClick={prev} aria-label="Previous workflow video">
          ← Prev
        </button>
        <div role="tablist" aria-label="Workflow videos">
          {SLIDES.map((s, i) => (
            <button
              key={s.title}
              type="button"
              role="tab"
              aria-selected={i === index}
              aria-label={`Show ${s.title} video`}
              className={i === index ? 'is-active' : ''}
              onClick={() => setIndex(i)}
            >
              {s.title}
            </button>
          ))}
        </div>
        <button type="button" onClick={next} aria-label="Next workflow video">
          Next →
        </button>
      </div>
    </div>
  );
}

export default HeroWorkflowShowcase;
