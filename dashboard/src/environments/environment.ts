export const environment = {
  production: false,
  apiUrl: 'http://localhost:8400/api',
  wsUrl: 'ws://localhost:8400/ws',
  identityProviders: {
    github: {
      clientId: 'github_client_id',
      redirectUri: 'http://localhost:4200/auth/callback'
    },
    gitlab: {
      clientId: 'gitlab_client_id',
      redirectUri: 'http://localhost:4200/auth/callback'
    },
    google: {
      clientId: 'google_client_id',
      redirectUri: 'http://localhost:4200/auth/callback'
    },
    microsoft: {
      clientId: 'microsoft_client_id',
      redirectUri: 'http://localhost:4200/auth/callback'
    }
  }
};