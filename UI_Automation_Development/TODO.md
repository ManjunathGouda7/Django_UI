# TODO - Django UI 404 Fix

- [ ] Add a root (`/`) URL route to prevent 404 when hitting the base server URL.
- [ ] Change Django `DEBUG` setting from `True` to `False` for standard 404 behavior.
- [x] Restart the Django dev server.

- [ ] Verify:
  - [ ] `GET /` returns expected message/response.
  - [ ] `GET /api/health/` returns success.

