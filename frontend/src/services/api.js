import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to inject the JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Authentication ──
export async function login(username, password) {
  const response = await api.post('/token/', { username, password });
  if (response.data.access) {
    localStorage.setItem('access_token', response.data.access);
    localStorage.setItem('refresh_token', response.data.refresh);
  }
  return response.data;
}

export function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  window.location.href = '/login';
}

// ── Jobs ──
export async function fetchJobs({ status, search } = {}) {
  const params = {};
  if (status) params.status = status;
  if (search) params.search = search;
  const response = await api.get('/jobs/', { params });
  return response.data;
}

export async function fetchJobDetail(jobId) {
  const response = await api.get(`/jobs/job/${jobId}/`);
  return response.data;
}

export async function createJob(data) {
  const response = await api.post('/jobs/create-job/', data);
  return response.data;
}

// ── Assignments ──
export async function assignTechnician(jobId, technicianId) {
  const response = await api.post(`/jobs/job/${jobId}/assign/`, {
    technician_id: technicianId,
  });
  return response.data;
}

export async function fetchAssignments({ status, job_id } = {}) {
  const params = {};
  if (status) params.status = status;
  if (job_id) params.job_id = job_id;
  const response = await api.get('/jobs/assignments/', { params });
  return response.data;
}

export async function fetchPendingReassignments() {
  const response = await api.get('/jobs/assignments/pending-reassignment/');
  return response.data;
}

export async function acceptAssignment(assignmentId) {
  const response = await api.post(`/jobs/assignments/${assignmentId}/accept/`);
  return response.data;
}

export async function rejectAssignment(assignmentId, reason = '') {
  const response = await api.post(`/jobs/assignments/${assignmentId}/reject/`, { reason });
  return response.data;
}

// ── Technicians ──
export async function fetchTechnicians({ availability, search } = {}) {
  const params = {};
  if (availability) params.availability = availability;
  if (search) params.search = search;
  const response = await api.get('/technicians/', { params });
  return response.data;
}

export async function fetchTechnicianDetail(id) {
  const response = await api.get(`/technicians/${id}/`);
  return response.data;
}

export async function createTechnician(data) {
  const response = await api.post('/technicians/add/', data);
  return response.data;
}

export async function updateTechnician(id, data) {
  const response = await api.patch(`/technicians/${id}/update/`, data);
  return response.data;
}

export async function deleteTechnician(id) {
  const response = await api.delete(`/technicians/${id}/delete/`);
  return response.data;
}

export async function importTechnicians(data) {
  const response = await api.post('/technicians/import/', data);
  return response.data;
}

export async function importTechniciansFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/technicians/import/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

// ── Warranty ──
export async function checkWarranty(serialNumber) {
  const response = await api.get(`/jobs/warranty/${serialNumber}/`);
  return response.data;
}

// ── Feedback ──
export async function fetchFeedback({ rating, technician } = {}) {
  const params = {};
  if (rating) params.rating = rating;
  if (technician) params.technician = technician;
  const response = await api.get('/jobs/feedback/', { params });
  return response.data;
}

// ── Reports ──
export async function fetchReports({ severity, resolved, technician } = {}) {
  const params = {};
  if (severity) params.severity = severity;
  if (resolved !== undefined) params.resolved = resolved;
  if (technician) params.technician = technician;
  const response = await api.get('/jobs/reports/', { params });
  return response.data;
}

export async function createReport(data) {
  const response = await api.post('/jobs/reports/create/', data);
  return response.data;
}

export async function resolveReport(id, actionTaken) {
  const response = await api.patch(`/jobs/reports/${id}/resolve/`, {
    action_taken: actionTaken,
  });
  return response.data;
}

// ── Conversations ──
export async function fetchConversations({ status } = {}) {
  const params = {};
  if (status) params.status = status;
  const response = await api.get('/jobs/conversations/', { params });
  return response.data;
}

export async function fetchConversationDetail(id) {
  const response = await api.get(`/jobs/conversations/${id}/`);
  return response.data;
}

export async function sendMessage(conversationId, content, senderType = 'agent') {
  const response = await api.post(`/jobs/conversations/${conversationId}/send/`, {
    content,
    sender_type: senderType,
  });
  return response.data;
}

export async function closeConversation(id, status = 'resolved') {
  const response = await api.post(`/jobs/conversations/${id}/close/`, { status });
  return response.data;
}

export default api;
