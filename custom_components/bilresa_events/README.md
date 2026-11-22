# BILRESA Early Release Events

An event-only adapter for the lighting pilot. It subscribes to Home Assistant's
existing Matter client, without a second Matter connection, device commands,
bindings, core patches or gesture timers. Select only the existing native Matter
lighting button event entities during the config flow.

Each selected button gets `event.<existing_object_id>_short_release`, exposing
only `short_release`, with `event_number`, `matter_timestamp`, and
`source_entity_id`. Native LongPress/LongRelease remain with the built-in Matter
integration. Position updates are not needed to emit a short release.

Repeated ShortRelease event numbers are rejected per node/endpoint. The last 512
accepted releases per endpoint are persisted across reloads. Persistence is
scheduled one second after receipt and never delays the action; a hard crash
inside that persistence window can lose the last identities. Events older than
the retained 512 are outside the replay protection window. Initial node
snapshots are never converted to actions. No synthetic live test events are sent.

The subscription is checked every five seconds to reattach after the core Matter
entry reloads. Buttons may be unavailable during that interval. There is no
device polling, classification wait, or fallback inferred from press duration.

Install this private repository as a Marketplace custom Integration repository,
then add `BILRESA Early Release Events`. A Core restart may be necessary for new
custom-component discovery. All-room routing is deployed separately through
HA-MCP only after the 22 entities have been verified.

Rollback: first restore the saved 22 automation configs with fresh hashes. Then
disable this adapter's config entry; that only removes its subscriptions/entities
and leaves native Matter and the original controls intact. No full HA restore.
