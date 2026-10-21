import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import AccordionSubnav from './AccordionSubnav';

// AccordionSubnav builds its sections from the active tab (the old test assumed
// generic "Section 1/Content 1" fixtures that the component never had).
describe('AccordionSubnav', () => {
  test('renders accordion navigation', () => {
    render(<AccordionSubnav activeTab="chat" />);
    expect(screen.getByRole('button', { name: /Conversation History/i })).toBeInTheDocument();
  });

  test('displays accordion sections', () => {
    render(<AccordionSubnav activeTab="chat" />);
    expect(screen.getByText(/Conversation History/i)).toBeInTheDocument();
    expect(screen.getByText(/Chat Settings/i)).toBeInTheDocument();
    expect(screen.getByText(/SBA Resources/i)).toBeInTheDocument();
  });

  test('expands and collapses sections', () => {
    render(<AccordionSubnav activeTab="chat" />);
    const header = screen.getByRole('button', { name: /Chat Settings/i });
    expect(header).toHaveClass('collapsed');
    fireEvent.click(header);
    expect(header).not.toHaveClass('collapsed');
    fireEvent.click(header);
    expect(header).toHaveClass('collapsed');
  });

  test('calls onSectionChange with the section and item', () => {
    const onSectionChange = jest.fn();
    render(<AccordionSubnav activeTab="sba" onSectionChange={onSectionChange} />);
    // First section is open by default
    fireEvent.click(screen.getByRole('button', { name: /7\(a\) Loans/i }));
    expect(onSectionChange).toHaveBeenCalledWith('SBA Programs', '7(a) Loans');
  });

  test('renders nothing for an unknown tab', () => {
    const { container } = render(<AccordionSubnav activeTab="nope" />);
    expect(container.querySelectorAll('.accordion-item')).toHaveLength(0);
  });
});
