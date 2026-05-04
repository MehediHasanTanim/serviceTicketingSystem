# Security

Contents:
- Auth and RBAC
- Audit logging
- Data privacy

## JWT Troubleshooting

If JWT login/refresh/logout fails, use this quick checklist.

1. Verify token shape
- Login and refresh responses must include: `access`, `refresh`, `access_expires_at`, `refresh_expires_at`.
- If the frontend expects `token` or `refresh_token`, update it to the JWT fields above.

2. Verify `Authorization` header format
- All protected calls must send: `Authorization: Bearer <access_jwt>`.
- Missing `Bearer` prefix or using a refresh token in place of access token causes `401`.

3. Verify refresh flow
- Refresh endpoint expects JSON body: `{"refresh_token":"<refresh_jwt>"}`.
- If token rotation is enabled, always replace stored refresh token with the latest returned one.

4. Verify logout behavior
- Logout revokes active refresh tokens for the user in the refresh-token store.
- Existing access token may remain usable until expiry; this is normal for stateless JWT unless access-token deny-listing is added.

5. Verify server secret and clock
- Use a strong `DJANGO_SECRET_KEY` (32+ chars recommended) to avoid weak-signing warnings.
- Ensure backend and client/container clocks are correct; clock skew can cause immediate token expiry errors.

6. Verify migrations and runtime config
- Run migrations after JWT/auth changes.
- Confirm backend uses the same env settings in Docker and local runs.
