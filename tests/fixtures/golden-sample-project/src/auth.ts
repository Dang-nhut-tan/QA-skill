export function login(username: string, password: string): string {
  if (!username || !password) {
    throw new Error('Credentials are required');
  }
  return 'dashboard';
}

