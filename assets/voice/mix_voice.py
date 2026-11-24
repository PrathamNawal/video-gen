import json, subprocess, sys
master, out = sys.argv[1], sys.argv[2]
beats = json.load(open('beats.json')); n = len(beats)
cmd = ['ffmpeg', '-y', '-loglevel', 'error']
for i in range(n): cmd += ['-i', f'beat{i:02d}.wav']
cmd += ['-i', master]
f = ''
for i, (t, _, _) in enumerate(beats):
    f += f'[{i}:a]aresample=44100,adelay={int(t*1000)}|{int(t*1000)}[v{i}];'
f += ''.join(f'[v{i}]' for i in range(n)) + f'amix=inputs={n}:normalize=0,apad=whole_dur=30,atrim=0:30,loudnorm=I=-16:TP=-1.5[voice];'
f += f'[{n}:a]volume=0.8[bg];[voice]asplit[v1][v2];[bg][v1]sidechaincompress=threshold=0.02:ratio=4:attack=20:release=250[duck];[duck][v2]amix=inputs=2:normalize=0,alimiter=limit=0.89,volume=0.9[mix]'
cmd += ['-filter_complex', f, '-map', f'{n}:v', '-map', '[mix]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', '30', '-movflags', '+faststart', out]
subprocess.run(cmd, check=True)
