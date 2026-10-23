import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';
import SBANavigation from '../SBANavigation';

jest.mock('../ConnectionStatusIndicator', () => () => <span>status</span>);

function setGeometry(el, { scrollWidth, clientWidth, scrollLeft = 0 }) {
  Object.defineProperty(el, 'scrollWidth', { configurable: true, value: scrollWidth });
  Object.defineProperty(el, 'clientWidth', { configurable: true, value: clientWidth });
  Object.defineProperty(el, 'scrollLeft', { configurable: true, writable: true, value: scrollLeft });
}

const renderNav = () =>
  render(
    <MemoryRouter initialEntries={['/chat']}>
      <SBANavigation serverConnected connectionStatus="online" />
    </MemoryRouter>
  );

describe('primary nav sideways-scroll cue', () => {
  test('no fade when everything fits (desktop)', () => {
    renderNav();
    const nav = screen.getByTestId('primary-nav');
    setGeometry(nav.querySelector('.pp-nav-inner'), { scrollWidth: 900, clientWidth: 1100 });
    act(() => { window.dispatchEvent(new Event('resize')); });
    expect(nav).not.toHaveClass('pp-nav--fade-right');
    expect(nav).not.toHaveClass('pp-nav--fade-left');
  });

  test('fades the right edge when links overflow, and the left edge once scrolled', () => {
    renderNav();
    const nav = screen.getByTestId('primary-nav');
    const scroller = nav.querySelector('.pp-nav-inner');
    setGeometry(scroller, { scrollWidth: 536, clientWidth: 390, scrollLeft: 0 });
    act(() => { window.dispatchEvent(new Event('resize')); });
    expect(nav).toHaveClass('pp-nav--fade-right');
    expect(nav).not.toHaveClass('pp-nav--fade-left');

    scroller.scrollLeft = 60;
    fireEvent.scroll(scroller);
    expect(nav).toHaveClass('pp-nav--fade-right');
    expect(nav).toHaveClass('pp-nav--fade-left');

    scroller.scrollLeft = 146; // scrolled to the end
    fireEvent.scroll(scroller);
    expect(nav).not.toHaveClass('pp-nav--fade-right');
    expect(nav).toHaveClass('pp-nav--fade-left');
  });
});
