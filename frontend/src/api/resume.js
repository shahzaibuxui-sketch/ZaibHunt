// src/api/resume.js
import client from './client';

export async function uploadResume(file) {
  const formData = new FormData();
  formData.append('resume', file);

  const response = await client.post('/resume/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data.resume;
}

export async function getMyResume() {
  try {
    const response = await client.get('/resume/me');
    return response.data.resume;
  } catch (error) {
    if (error.response && error.response.status === 404) {
      return null;
    }
    throw error;
  }
}