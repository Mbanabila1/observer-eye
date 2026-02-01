export interface User {
  id: string;
  username: string;
  email: string;
  identityProvider: string;
  externalId: string;
  lastLogin?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface UserSession {
  id: string;
  userId: string;
  sessionToken: string;
  expiresAt: Date;
  ipAddress: string;
  userAgent: string;
}

export interface IdentityProvider {
  name: string;
  clientId: string;
  authorizationUrl: string;
  tokenUrl: string;
  userInfoUrl: string;
  isActive: boolean;
}

export enum IdentityProviderType {
  GITHUB = 'github',
  GITLAB = 'gitlab',
  GOOGLE = 'google',
  MICROSOFT = 'microsoft'
}