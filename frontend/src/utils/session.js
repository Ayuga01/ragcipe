export function getSessionId() {
  let sessionId = localStorage.getItem('ragcipe_session_id');
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem('ragcipe_session_id', sessionId);
  }
  return sessionId;
}

