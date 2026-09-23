# Network contract — 4M

Every RemoteEvent and RemoteFunction is listed here. A PR that adds or changes a remote updates this file in the same PR.

## Rules

- Remotes are created only in `src/shared/Net/`.
- The server validates **every** argument from the client: type, range, ownership (does this player own this item?), and rate (how often per second).
- Prefer RemoteEvents. Never use `RemoteFunction:InvokeClient` — a client can hang the server thread.
- Payloads are small and flat. Send IDs, not instances or whole tables of state.
- Use UnreliableRemoteEvent only for high-frequency cosmetic data that may be dropped.

## Remotes

| Name | Type | Direction | Payload | Server validation | Owner |
|------|------|-----------|---------|-------------------|-------|
| _none yet_ | | | | | |

Direction: `C→S` client to server, `S→C` server to client, `S→All` broadcast.
