import React from 'react';
import { render, screen } from '@testing-library/react';
import RagProcessPanel, {
  dedupeSources,
  extraLinksFromContent,
} from './RagProcessPanel';

describe('RagProcessPanel', () => {
  it('is idle before any question, with no sources', () => {
    render(<RagProcessPanel query="" stage="idle" sources={[]} />);
    expect(screen.getByText(/Ask a question in the chat above/i)).toBeInTheDocument();
    expect(screen.queryByText(/Sources used for this answer/i)).not.toBeInTheDocument();
  });

  it('shows the query and the retrieving stage while a request runs', () => {
    render(<RagProcessPanel query="What does my lease say?" stage="retrieving" sources={[]} />);
    expect(screen.getByText(/Query received: “What does my lease say\?”/)).toBeInTheDocument();
    expect(screen.getByText(/Retrieving…/)).toBeInTheDocument();
  });

  it('deduplicates retrieved sources and counts only distinct ones', () => {
    const sources = [
      { title: 'Lease.txt', path: '/documents' },
      { title: 'Lease.txt', path: '/documents' },
      { title: 'SBA Loans', path: '/api/sba/content/loans' },
    ];
    expect(dedupeSources(sources)).toHaveLength(2);
    render(<RagProcessPanel query="loans" stage="answered" sources={sources} />);
    expect(screen.getByText(/Retrieved 2 sources/)).toBeInTheDocument();
    expect(screen.getAllByText('Lease.txt')).toHaveLength(1);
  });

  it('shows a failed stage with the error, and no invented sources', () => {
    render(<RagProcessPanel query="loans" stage="failed" sources={[]} error="Chat went down" />);
    expect(screen.getByText(/Failed/)).toBeInTheDocument();
    expect(screen.getByText(/Chat went down/)).toBeInTheDocument();
    expect(screen.queryByText(/Sources used for this answer/i)).not.toBeInTheDocument();
  });

  it('extra links exclude links already shown in the panel', () => {
    const shown = [{ label: 'SBA Loans', href: '/browse' }];
    const content = 'See [SBA Loans](/browse) and [SBA 7(a)](https://www.sba.gov/funding-programs/loans/7a-loans).';
    const more = extraLinksFromContent(content, shown);
    expect(more).toHaveLength(1);
    expect(more[0].label).toBe('SBA 7(a)');
  });
});
