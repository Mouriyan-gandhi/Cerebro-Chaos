const API_BASE = 'http://localhost:8000/api';

class ApiService {
  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      if (error.message === 'Failed to fetch') {
        throw new Error('Cannot connect to backend. Ensure the server is running on port 8000.');
      }
      throw error;
    }
  }

  // Repository endpoints
  async analyzeRepo(url, branch = 'main') {
    return this.request('/repos/analyze', {
      method: 'POST',
      body: JSON.stringify({ url, branch }),
    });
  }

  async listRepos() {
    return this.request('/repos');
  }

  async getRepo(repoId) {
    return this.request(`/repos/${repoId}`);
  }

  async deleteRepo(repoId) {
    return this.request(`/repos/${repoId}`, { method: 'DELETE' });
  }

  // Dependency graph
  async getGraph(repoId) {
    return this.request(`/repos/${repoId}/graph`);
  }

  // Risks
  async getRisks(repoId) {
    return this.request(`/repos/${repoId}/risks`);
  }

  async getFixSuggestion(riskId) {
    return this.request(`/risks/${riskId}/fix`);
  }

  // Chaos tests
  async runChaosTest(repoId, testData) {
    return this.request(`/repos/${repoId}/chaos`, {
      method: 'POST',
      body: JSON.stringify(testData),
    });
  }

  async listChaosTests(repoId) {
    return this.request(`/repos/${repoId}/chaos`);
  }

  // Dashboard
  async getDashboardStats() {
    return this.request('/dashboard/stats');
  }
}

export const api = new ApiService();
export default api;
