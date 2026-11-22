# Closer: credits and sources

A film about how Amazon CloudFront works. Made entirely in code (Skia, Python). No photographs, no stock footage.
This is an independent explainer. It is not made by or endorsed by Amazon or AWS.

## Facts
- Launch in November 2008 with 14 edge locations (8 US, 4 Europe, 2 Asia): AWS blog, "98, 99, 100 CloudFront Points of Presence" and the 15th-anniversary post.
- "More than 600 points of presence": AWS's own description of the network (also 13 regional edge caches, 100+ cities, 50 countries). Wikipedia's higher figure (1,600+) disagrees with AWS, so the film uses AWS's.
- Request routing, edge, regional edge cache, origin, and collapsing of simultaneous requests: AWS CloudFront Developer Guide, "How CloudFront delivers content".
- Mumbai to Virginia: about 12,855 km (great-circle, computed from city coordinates; Ashburn is used as a stand-in for "Virginia"). Light in fibre travels at about 200,000 km/s, so the round trip is at least ~129 ms.

## Things in the film that are illustrative, not data
- The positions of the 14 launch locations and of the 600+ swarm are drawn for effect and are labelled "locations illustrative" on screen. They are not real edge-location coordinates.
- The short hop next to Mumbai is an illustrative nearby edge.
- The pipeline devices (phone, DNS card, racks, origin) are simplified drawings.
- Left out for brevity: dynamic requests and PUT/POST/PATCH/OPTIONS/DELETE go straight to the origin, and cache lifetime comes from TTL settings and cache-control headers.

## Assets
- Land shapes: Natural Earth countries (public domain), via the `world-atlas` npm package (ISC licence).
- Type: Bebas Neue (SIL Open Font License 1.1), see `fonts/LICENSES.txt`.
- Voice: Piper TTS with the `en_US-ryan-high` voice from `rhasspy/piper-voices`. Check that voice's model card for its licence before using the film commercially.
- Music and sound effects: synthesised from scratch in numpy (`make_score.py`, `build_sfx.py`). No samples.
