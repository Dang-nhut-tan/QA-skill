export class LoginPage {
  async login(username: string, password: string): Promise<string> {
    if (!username || !password) throw new Error('Credentials are required');
    return 'dashboard';
  }
}

