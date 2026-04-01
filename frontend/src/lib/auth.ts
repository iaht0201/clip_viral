export const auth = {
  api: {
    getSession: async () => ({
      user: {
        id: "local_user",
        name: "Local User",
        email: "local@supoclip.com",
        is_admin: true,
      },
      session: {
        id: "mock_session",
      }
    })
  }
} as any;

export type Session = any;
