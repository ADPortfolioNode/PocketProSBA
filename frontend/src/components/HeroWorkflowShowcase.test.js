import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import HeroWorkflowShowcase from './HeroWorkflowShowcase';

const renderShowcase = () =>
  render(
    <MemoryRouter>
      <HeroWorkflowShowcase />
    </MemoryRouter>,
  );

describe('HeroWorkflowShowcase', () => {
  test('shows one workflow video at a time, muted until clicked', () => {
    const { container } = renderShowcase();
    const video = container.querySelector('video');
    expect(video).toBeInTheDocument();
    expect(video).toHaveAttribute('src', '/demo-videos/programs.mp4');
    expect(video.muted).toBe(true);
    expect(screen.getByRole('heading', { name: 'Programs' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Try Programs/ })).toHaveAttribute('href', '/sba');
  });

  test('slides are modular: stepping to the next slide swaps the workflow', () => {
    const { container } = renderShowcase();
    fireEvent.click(screen.getByRole('button', { name: 'Next workflow video' }));
    expect(container.querySelector('video')).toHaveAttribute('src', '/demo-videos/browse.mp4');
    expect(screen.getByRole('heading', { name: 'Browse resources' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('tab', { name: 'Show Chat concierge video' }));
    expect(container.querySelector('video')).toHaveAttribute('src', '/demo-videos/chat.mp4');
  });

  test('clicking the video toggles sound on', () => {
    const { container } = renderShowcase();
    expect(screen.getByRole('button', { name: 'Turn video sound on' })).toBeInTheDocument();
    fireEvent.click(container.querySelector('video'));
    expect(screen.getByRole('button', { name: 'Mute video' })).toBeInTheDocument();
  });
});
