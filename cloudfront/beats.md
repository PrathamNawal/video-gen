# Closer: beat table

18 lines, 1:22.2 total, ESTIMATED from letter counts (no voice yet).

Hero = the one thing the camera is on (everything else dims). Typed = text drawn in code; a phrase is either typed or shown on a real document, never both.

| # | Start | Len | Narration | Hero on screen | Typed |
|---|---|---|---|---|---|
| 1 | 0:00.9 | 3.6s | You press play in Mumbai. The video lives on a server in Virginia. | globe: a glowing dot in Mumbai, a dot in Virginia, an arc drawing across the ocean | MUMBAI → VIRGINIA |
| 2 | 0:04.8 | 2.9s | That is almost thirteen thousand kilometres away. | the arc stretches; a distance counter rolls up | 12,855 KM |
| 3 | 0:08.1 | 4.4s | Even at the speed of light in fibre, the round trip takes over a tenth of a second. | a light pulse runs out along the arc and back; a stopwatch counts | 130 ms+ |
| 4 | 0:13.0 | 2.7s | Amazon CloudFront exists to shorten that trip. | the arc snaps short; the title lands | CLOSER |
| 5 | 0:16.5 | 4.0s | The idea is simple. Do not make the file travel. Put a copy near the viewer. | one file icon in Virginia splits into copies that fly out to cities | COPY → NEAR YOU |
| 6 | 0:20.9 | 4.4s | In two thousand eight, CloudFront launched with fourteen of these locations. | fourteen glowing dots on the globe (8 US, 4 Europe, 2 Asia); counter | 2008 · 14 |
| 7 | 0:25.8 | 4.6s | Today there are more than six hundred points of presence, in over a hundred cities. | the globe floods with dots; counter rolls up | 600+ |
| 8 | 0:30.9 | 4.2s | Here is the journey of one request. Your phone asks DNS where the file lives. | phone illustration; a DNS lookup card slides in beside it | DNS |
| 9 | 0:35.5 | 4.4s | DNS answers with a nearby edge location, the one that should be fastest for you. | the phone's request lights up the nearest edge among several; the others dim | NEAREST EDGE |
| 10 | 0:40.4 | 4.1s | The edge checks its cache. If the file is there, that is a hit, and you are done. | edge rack with shelves; the file is on a shelf; green stamp; file flies back to phone | CACHE HIT |
| 11 | 0:45.0 | 4.9s | If it is not, that is a miss. The edge asks a regional edge cache, a bigger shelf one layer up. | empty shelf; red stamp; request climbs to a larger regional cache | CACHE MISS |
| 12 | 0:50.3 | 4.1s | Still nothing? Only then does the request travel all the way to the origin. | the long arc to Virginia lights up; the origin server glows | ORIGIN |
| 13 | 0:54.9 | 3.9s | The origin sends the file back, and every layer on the way keeps a copy. | the file travels back; copies drop onto the regional and edge shelves | -- |
| 14 | 0:59.2 | 2.0s | The next viewer in Mumbai gets a hit. | a second phone asks; the file flies from the nearby shelf almost instantly | HIT |
| 15 | 1:01.8 | 5.4s | And if a thousand people ask at once, CloudFront merges them into a single request to the origin. | a crowd of request dots funnel into one line to the origin | 1,000 → 1 |
| 16 | 1:07.7 | 4.1s | Each copy stays fresh for a set time. When it expires, the edge checks again. | a countdown ring on the shelf copy; it empties, then refills | TTL |
| 17 | 1:12.2 | 2.5s | The origin works less. The viewer waits less. | two bars shrink side by side | LESS LOAD · LESS WAIT |
| 18 | 1:15.2 | 3.6s | The video was never really in Virginia. It was already next door. | pull back over the whole globe: the long arc fades, the short arc stays bright | -- |
