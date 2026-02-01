export const environment = {
  production: true,
  apiUrl: '/api',
  wsUrl: '/ws',
  identityProviders: {
    github: {
      clientId: process.env['GITHUB_CLIENT_ID'] || '',
      redirectUri: `${window.location.origin}/auth/callback`
    },
    gitlab: {
      clientId: process.env['GITLAB_CLIENT_ID'] || '',
      redirectUri: `${window.location.origin}/auth/callback`
    },
    google: {
      clientId: process.env['GOOGLE_CLIENT_ID'] || '',
      redirectUri: `${window.location.origin}/auth/callback`
    },
    microsoft: {
      clientId: process.env['MICROSOFT_CLIENT_ID'] || '',
      redirectUri: `${window.location.origin}/auth/callback`
    }
  }
};