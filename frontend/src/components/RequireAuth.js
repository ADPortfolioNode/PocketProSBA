import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useSession } from '../hooks/useSession';
import { loginPathFor } from '../utils/authStorage';

/** Tabs that call protected API routes (chat/LLM, RAG + tasks, document uploads). */
export const PROTECTED_TABS = new Set(['chat', 'rag', 'documents', 'orchestrator']);

/**
 * Route guard: renders children for a signed-in user, otherwise sends them to
 * /login?next=<this page> so they land back here after logging in.
 */
function RequireAuth({ children }) {
  const { authenticated } = useSession();
  const location = useLocation();
  if (!authenticated) {
    const here = `${location.pathname}${location.search || ''}${location.hash || ''}`;
    return <Navigate to={loginPathFor(here)} replace />;
  }
  return children;
}

export default RequireAuth;
