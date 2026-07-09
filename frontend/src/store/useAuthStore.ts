import { create } from 'zustand';

interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: 'ADMIN' | 'USER';
}

interface AuthState {
  token: string | null;
  user: UserProfile | null;
  isAuthenticated: boolean;
  setAuth: (token: string, user: UserProfile) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => {
  // Read initial states from localStorage
  const cachedToken = localStorage.getItem('auth_token');
  const cachedUserRaw = localStorage.getItem('auth_user');
  let cachedUser: UserProfile | null = null;
  
  if (cachedUserRaw) {
    try {
      cachedUser = JSON.parse(cachedUserRaw);
      if (cachedUser && cachedUser.role !== 'USER' && cachedUser.role !== 'ADMIN') {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        cachedUser = null;
      }
    } catch {
      localStorage.removeItem('auth_user');
    }
  }

  const hasToken = !!cachedUser && !!localStorage.getItem('auth_token');

  return {
    token: cachedUser ? cachedToken : null,
    user: cachedUser,
    isAuthenticated: hasToken,

    setAuth: (token, user) => {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_user', JSON.stringify(user));
      set({ token, user, isAuthenticated: true });
    },

    logout: () => {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      set({ token: null, user: null, isAuthenticated: false });
    },
  };
});
