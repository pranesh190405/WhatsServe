import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Fetch all jobs, with optional status filter and search query.
 */
export async function fetchJobs({ status, search } = {}) {
  const params = {};
  if (status) params.status = status;
  if (search) params.search = search;

  const response = await api.get('/jobs/', { params });
  return response.data;
}

/**
 * Fetch a single job by its human-readable job_id.
 */
export async function fetchJobDetail(jobId) {
  const response = await api.get(`/jobs/job/${jobId}/`);
  return response.data;
}

/**
 * Create a new service job.
 */
export async function createJob(data) {
  const response = await api.post('/jobs/create-job/', data);
  return response.data;
}

/**
 * Check warranty by serial number.
 */
export async function checkWarranty(serialNumber) {
  const response = await api.get(`/jobs/warranty/${serialNumber}/`);
  return response.data;
}

export default api;
