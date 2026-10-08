import axios from 'axios';

const API = axios.create({ baseURL: 'http://localhost:8000' });

export const uploadFile = (file) => {
  const form = new FormData();
  form.append('file', file);
  return API.post('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const sendMessage = (session_id, question) =>
  API.post('/chat', { session_id, question });

export const clearSession = (session_id) =>
  API.delete(`/session/${session_id}`);
