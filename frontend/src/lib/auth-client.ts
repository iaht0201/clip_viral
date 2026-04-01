export const authClient = {} as any;

export const signIn = async () => ({ data: null, error: null });
export const signOut = async () => ({ data: null, error: null });
export const signUp = async () => ({ data: null, error: null });
export const useSession = () => ({
  data: {
    user: {
      id: "local_user",
      name: "Local User",
      email: "local@supoclip.com",
      is_admin: true,
      image: null
    },
    session: {
      id: "local_session",
      userId: "local_user",
      expiresAt: new Date(2099, 1, 1),
      createdAt: new Date(),
      updatedAt: new Date(),
      ipAddress: "127.0.0.1",
      userAgent: "local"
    }
  },
  isPending: false,
  error: null
});
