import { apiRequest } from './client';
import { User } from '../types/auth';

export async function login(username: string, password: string):Promise<User> {
  const data = await apiRequest<{ user: User }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  return data.user;
}

export async function logout(): Promise<void> {
  await apiRequest('/auth/logout', { method: 'POST' });
}

export async function getCurrentUser(): Promise<User> {
  const data = await apiRequest<{ user: User }>('/auth/me');
  return data.user;
}
