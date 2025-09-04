import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import AccordionSubnav from './AccordionSubnav';

describe('AccordionSubnav', () => {
  test('renders accordion navigation', () => {
    render(<AccordionSubnav />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  test('displays accordion sections', () => {
    render(<AccordionSubnav />);
    expect(screen.getByText(/section 1/i)).toBeInTheDocument();
    expect(screen.getByText(/section 2/i)).toBeInTheDocument();
  });

  test('expands and collapses sections', () => {
    render(<AccordionSubnav />);
    const button = screen.getByRole('button');
    fireEvent.click(button);
    expect(screen.getByText(/content 1/i)).toBeVisible();
  });

  test('handles multiple section expansion', () => {
    render(<AccordionSubnav />);
    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => fireEvent.click(button));
    expect(screen.getByText(/content 1/i)).toBeVisible();
    expect(screen.getByText(/content 2/i)).toBeVisible();
  });
});
