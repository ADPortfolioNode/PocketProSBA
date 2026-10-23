import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import fs from 'fs';
import path from 'path';
import RAGWorkflowInterface from '../components/RAGWorkflowInterface';
import TaskOrchestrator from '../components/TaskOrchestrator';

jest.mock('../api/apiClient');

describe('form labels are associated with their inputs', () => {
  test('RAG workflow: the file input has an accessible name', () => {
    render(<RAGWorkflowInterface />);
    expect(screen.getByLabelText(/Select a file to upload/i)).toHaveAttribute('type', 'file');
  });

  test('Task orchestrator: the task description textarea is labelled', () => {
    render(<TaskOrchestrator />);
    expect(screen.getByLabelText(/Task Description/i).tagName).toBe('TEXTAREA');
  });
});

test('auth links get at least 44px tap targets', () => {
  const css = fs.readFileSync(path.join(__dirname, '..', 'App.css'), 'utf8');
  const rule = css.match(/\.container-centered \.auth-links a \{([^}]*)\}/);
  expect(rule).not.toBeNull();
  expect(rule[1]).toMatch(/min-height:\s*44px/);
  expect(rule[1]).toMatch(/min-width:\s*44px/);
});
