#!/usr/bin/env python3
"""Trilha do reel da Central Fiscal — 128 BPM, 24 compassos = 45 s, sintetizada do zero.

Cada evento sonoro está preso a um evento visual do reel.html (mesmos tempos).
Instrumentos e mixagem vêm do showreel do órbita (horbita/showreel/audio).
Uso:  python3 soundtrack.py saida.wav
"""
import sys
import wave
import numpy as np
from scipy import signal
from synth import (SR, Mix, n_of, tt, midi, env, ar, sine, saw, noise, pink, filt, sweep, logline,
                   fm_bell, pluck, supersaw, reverb_ir)

BPM, DUR = 128, 45.0
BEAT = 60 / BPM
B = lambda n: n * BEAT
M = Mix(DUR)


# ================= instrumentos =================
def kick(f0=160, f1=45, ad=0.34, click=0.5):
    n = n_of(ad * 2.2)
    t = tt(n)
    f = f1 + (f0 - f1) * np.exp(-t / 0.032)
    body = np.tanh(1.7 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / ad))
    cl = filt(noise(n), 'hp', 2500) * np.exp(-t / 0.0025) * click
    return body + cl


def clap():
    n = n_of(0.35)
    t = tt(n)
    e = sum(np.exp(-np.clip(t - d, 0, None) / 0.006) * (t >= d) for d in (0, 0.009, 0.018))
    e = e + 0.55 * np.exp(-np.clip(t - 0.024, 0, None) / 0.085) * (t >= 0.024)
    return filt(filt(noise(n), 'bp', 1300, 0.9), 'hp', 600) * e * 1.6


def snare(f=190, dec=0.12):
    n = n_of(0.3)
    t = tt(n)
    return np.sin(2 * np.pi * f * t) * np.exp(-t / 0.05) * 0.6 + filt(noise(n), 'bp', 2400, 0.7) * np.exp(-t / dec)


def hat(open_=False):
    n = n_of(0.3 if open_ else 0.06)
    t = tt(n)
    return filt(filt(noise(n), 'hp', 7500), 'peak', 10000, 1, 4) * np.exp(-t / (0.11 if open_ else 0.018))


def click(f=2600, d=0.012):
    n = n_of(d)
    t = tt(n)
    return (filt(noise(n), 'bp', f, 1.5) + np.sin(2 * np.pi * f * t) * 0.6) * np.exp(-t / (d / 4))


def thock(f=150):
    n = n_of(0.25)
    t = tt(n)
    fr = f * (1 + 0.6 * np.exp(-t / 0.012))
    body = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / 0.07)
    c = click(3200, 0.01)
    body[:len(c)] += c * 0.5
    return body


def whoosh(d, f0, f1, q=0.9, peak=0.7, color='white'):
    n = n_of(d)
    x = pink(n) if color == 'pink' else noise(n)
    y = sweep(x, 'bp', logline(f0, f1, n), q)
    u = np.linspace(0, 1, n)
    e = np.where(u < peak, (u / peak) ** 2, ((1 - u) / (1 - peak)) ** 1.5)
    return y * e


def zipper(d=0.2, f0=2600, f1=220):
    n = n_of(d)
    y = saw(logline(f0, f1, n, 0.7), n) * env(n, 0.002, d / 3)
    return filt(y, 'lp', 5000)


def sub(freq, d, a=0.01, r=0.06, drive=1.3):
    n = n_of(d)
    return np.tanh(drive * sine(freq, n)) * ar(n, a, r, 1.0)


def boom(f0=70, f1=32, d=1.6, dec=0.55):
    n = n_of(d)
    t = tt(n)
    f = f1 + (f0 - f1) * np.exp(-t / 0.25)
    return np.tanh(1.4 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t / dec)


def crash(d=1.8, dec=0.7):
    n = n_of(d)
    t = tt(n)
    return filt(noise(n), 'hp', 2800) * np.exp(-t / dec) * ar(n, 0.002, 0.3, 1)


def riser(d, f0=180, f1=1400, g=1.0):
    n = n_of(d)
    u = np.linspace(0, 1, n)
    x = sweep(noise(n), 'bp', logline(500, 9000, n, 1.6), 0.8) * u ** 2.2
    s = saw(logline(f0, f1, n, 1.5), n) * u ** 2.6 * 0.25
    return (x + filt(s, 'lp', 4000)) * g * ar(n, 0.01, 0.01, 1)


def reverse_swell(d=0.5):
    y = crash(d, d / 2.5)[::-1]
    return y * ar(len(y), 0.01, 0.004, 1)


def blip_down(f0=1400, f1=260, d=0.09):
    n = n_of(d)
    return sine(logline(f0, f1, n), n) * env(n, 0.001, d / 3)


def ratchet(t0, t1, rate0, rate1, gain, pan=0.0, f=4200):
    t = t0
    while t < t1:
        u = (t - t0) / max(t1 - t0, 1e-6)
        M.add(click(f, 0.006), t, gain * (0.6 + 0.4 * u), pan)
        t += 1 / (rate0 + (rate1 - rate0) * u)


def pad(chord, t0, d, gain, cut0, cut1, bus='pump', send=0.25, a=0.25, r=0.4):
    n = n_of(d)
    y = supersaw([midi(m) for m in chord], d)
    y = sweep(y, 'lp', logline(cut0, cut1, n), 0.8) * ar(n, a, r, 1.4)
    M.add(y, t0, gain * 0.8, -0.25, bus, send)
    y2 = supersaw([midi(m) for m in chord], d)
    y2 = sweep(y2, 'lp', logline(cut0, cut1, n), 0.8) * ar(n, a, r, 1.4)
    M.add(y2, t0, gain * 0.8, 0.25, bus, send)


# ================= utilidades de arranjo =================
PLANET = [76, 79, 81, 83, 84, 86, 88, 91]          # uma nota por ferramenta (a mesma do core.js)
PAN8 = [-0.6, -0.42, -0.25, -0.08, 0.08, 0.25, 0.42, 0.6]
G = np.random.default_rng(45)
TOOL0, TLEN = B(24), B(6)


def chord(notes, t0, gain, pan0=-0.4, spread=0.2, up=12, d=1.4, step=0.01, send=0.4):
    for i, m in enumerate(notes):
        M.add(pluck(midi(m + up), d, 1.3, 0.4), t0 + i * step, gain, pan0 + i * spread, 'dry', send)


def ticks(t0, t1, n, gain, f=3800, pan=(-0.4, 0.4)):
    for i in range(n):
        tk = t0 + (t1 - t0) * i / max(n - 1, 1)
        M.add(click(f + G.uniform(-400, 400), 0.008), tk, gain, G.uniform(*pan))


# ================= compassos 1–2 · IGNIÇÃO =================
M.add(boom(64, 38, 1.8, 0.7), 0.12, 0.32, 0, 'dry', 0.25)
M.add(fm_bell(midi(93), 2.0, 3.01, 1.2, 0.8), 0.12, 0.07, 0, 'dry', 0.8)
M.add(thock(120), B(1), 0.2)
M.add(whoosh(0.4, 300, 5200, 1.0, 0.85), B(1) - 0.02, 0.16)
for i in range(43):                                      # régua, do centro para fora
    tk = B(1) + 0.38 * (1 - (1 - i / 42) ** 3)
    M.add(click(5200 if i % 5 == 0 else 7000, 0.008), tk, 0.07 if i % 5 == 0 else 0.03, -0.9 + 1.8 * (i % 2))
M.add(whoosh(0.45, 2600, 420, 0.9, 0.55), B(1.55), 0.16, np.linspace(-0.6, 0.6, n_of(0.45)))
for i, m in enumerate((69, 72, 76)):                    # a marca: três estouros = três notas
    tp = B(2) + i * B(0.25)
    M.add(pluck(midi(m), 1.3, 1.0, 0.4), tp, 0.34, (-0.2, 0.15, -0.02)[i], 'dry', 0.45)
    M.add(boom(120, 60, 0.3, 0.08), tp, 0.13)
M.add(crash(1.0, 0.3), B(2), 0.05, 0, 'dry', 0.3)
M.add(whoosh(0.5, 700, 3000, 0.9, 0.5, 'pink'), B(3.2), 0.1)
ticks(B(4.4), B(4.4) + 0.35, 14, 0.03, 4400)
M.add(whoosh(0.5, 900, 7000, 1.1, 0.7), B(6.3), 0.2, np.linspace(0.3, -0.85, n_of(0.5)))
pad([57, 64, 67, 71, 72], 0.0, B(8) - 0.03, 0.16, 320, 1900, 'dry', 0.4, 0.9, 0.08)
M.add(sub(midi(33), B(8) - 1.0, 0.9, 0.05, 1.6), 1.0, 0.1)
M.add(riser(0.7, 160, 1200, 0.8), B(8) - 0.72, 0.18)

# ================= compassos 3–4 · MANIFESTO =================
for b in range(8, 16):
    M.add(kick(110, 45, 0.16, 0.2), B(b), 0.34 if b < 12 else 0.2)
for tw, f in ((B(8), 150), (B(8.75), 170), (B(9.5), 140), (B(10), 190)):  # cada palavra bate
    M.add(thock(f), tw, 0.3, 0, 'dry', 0.1)
    M.add(snare(200, 0.1), tw, 0.12, 0, 'dry', 0.2)
    M.add(boom(90, 44, 0.5, 0.14), tw, 0.16)
for i in range(4):                                      # o risco em cada palavra
    M.add(zipper(0.2), B(10.6) + i * 0.06, 0.09, -0.5 + i * 0.33)
M.add(reverse_swell(0.5), B(11.25) - 0.5, 0.1)
sw = n_of(1.1)
M.add(whoosh(1.1, 400, 3600, 0.8, 0.5, 'pink') * (0.7 + 0.3 * np.sin(np.linspace(0, 16, sw))), B(11.25), 0.16, 0.7 * np.sin(np.linspace(0, 10, sw)))
chord([57, 60, 64, 67, 71], B(13.2), 0.13)
M.add(fm_bell(midi(88), 2.4, 3.5, 1.2, 1.4), B(13.2), 0.06, 0.2, 'dry', 0.7)
pad([53, 57, 60, 64, 67], B(12), B(4), 0.14, 500, 2600, 'dry', 0.45, 0.4, 0.05)
for k in range(16):
    M.add(hat(), B(12) + k * B(0.25), 0.05 if k % 2 else 0.07, 0.25 if k % 2 else -0.15)
for k, tr in enumerate(B(15) + np.arange(8) * B(0.125)):
    M.add(snare(210 + k * 10, 0.08), tr, 0.05 + 0.025 * k, 0, 'drums', 0.1)
M.add(riser(0.75, 160, 1500, 1.0), B(16) - 0.78, 0.3)
M.add(whoosh(0.36, 3200, 300, 0.9, 0.85), B(16) - 0.38, 0.18)

# ================= compassos 5–18 · o groove =================
KICKS = [b for b in range(16, 72)] + [b for b in range(72, 80)]
PROG = [([53, 57, 60, 64, 67], 29), ([55, 59, 62, 64, 69], 31), ([57, 60, 64, 67, 71], 33), ([52, 55, 59, 62, 67], 28)]
for b in KICKS:
    M.add(kick(), B(b), 0.9, 0, 'drums')
for b in range(16, 80):
    if b % 2 == 1:
        M.add(clap(), B(b), 0.4, 0.05, 'drums', 0.2)
    M.add(hat(True), B(b + 0.5), 0.11, 0.2, 'drums')
    for s in (0.25, 0.75):
        M.add(hat(), B(b + s), 0.045, -0.25, 'drums')
for k, b0 in enumerate(range(16, 80, 4)):
    ch, root = PROG[k % 4]
    pad(ch, B(b0), B(4) + 0.05, 0.14, 1400, 2400, 'pump', 0.2, 0.02, 0.05)
    for e in range(8):
        m = root + (12 if e % 2 else 0)
        bl = sub(midi(m + 12), B(0.5) * 0.92, 0.004, 0.03, 2.6) * 0.8 + sub(midi(m), B(0.5) * 0.92, 0.004, 0.03, 1.2) * 0.7
        bl = bl + filt(saw(midi(m + 24), len(bl)), 'lp', 900) * ar(len(bl), 0.004, 0.05) * 0.18
        M.add(bl, B(b0 + e * 0.5), 0.26, 0, 'pump')

# drop
M.add(kick(170, 42, 0.5, 0.8), B(16), 0.6, 0, 'drums')
M.add(boom(62, 30, 2.0, 0.6), B(16), 0.38)
M.add(crash(2.2, 0.8), B(16), 0.14, 0, 'dry', 0.35)
M.add(fm_bell(midi(77), 2.5, 3.5, 1.2, 1.4), B(16), 0.06, -0.3, 'dry', 0.7)
M.add(fm_bell(midi(84), 2.5, 3.5, 1.2, 1.4), B(16) + 0.02, 0.05, 0.3, 'dry', 0.7)
for k in range(8):                                      # cada planeta nasce com a sua nota
    tp = B(17) + k * B(0.5)
    M.add(pluck(midi(PLANET[k]), 1.0, 1.1, 0.3), tp, 0.22, PAN8[k], 'dry', 0.4)
    M.add(blip_down(260, 120, 0.05), tp, 0.1, PAN8[k])
M.add(whoosh(0.6, 500, 2600, 0.9, 0.5), B(19.5), 0.08)
M.add(riser(B(1.55), 150, 1800, 1.0), B(22.3), 0.26)       # mergulho
M.add(whoosh(B(1.6), 150, 8000, 0.7, 0.93), B(22.3), 0.4, np.linspace(0.3, -0.3, n_of(B(1.6))))

# ================= ferramentas =================
for i in range(8):
    T0 = TOOL0 + i * TLEN
    tn = PLANET[i]
    M.add(boom(90, 42, 0.8, 0.22), T0, 0.2 if i else 0.3)
    M.add(crash(0.9, 0.25), T0, 0.04, 0, 'dry', 0.3)
    M.add(fm_bell(midi(tn), 1.8, 3.5, 1.1, 0.9), T0, 0.06, PAN8[i], 'dry', 0.6)
    M.add(whoosh(0.5, 2400, 300, 0.9, 0.35), T0, 0.1, np.linspace(0.6, -0.6, n_of(0.5)))
    if i < 7:
        M.add(whoosh(0.42, 250, 6000, 0.9, 0.95), T0 + TLEN - 0.42, 0.22, np.linspace(-0.3, 0.5, n_of(0.42)))
    ticks(T0 + 0.24, T0 + 0.6, 10, 0.022, 5200)          # o nome sobe
    for j in range(3):                                  # os três números rolam
        ratchet(T0 + 0.55 + j * 0.08, T0 + 1.35 + j * 0.08, 55, 12, 0.02, -0.5 + j * 0.3)

T = lambda i, u: TOOL0 + i * TLEN + u
# T·01 Fiscalbot — registros pousando nas caixas
for k in range(60):
    M.add(click(2600 + G.uniform(-300, 900), 0.01), T(0, 0.95 + k * 0.024), 0.03, G.uniform(-0.5, 0.5))
# T·02 Apurabot — o encaixe da carga
ns = n_of(0.5)
M.add(sine(logline(300, 2400, ns), ns) * ar(ns, 0.02, 0.1) * 0.6, T(1, 1.15), 0.08, np.linspace(-0.6, 0.6, ns))
chord([60, 64, 67, 71, 74], T(1, 1.45), 0.12, step=0.03)
for j in range(7):
    M.add(pluck(midi(84 + (0, 2, 4, 7, 9, 12, 14)[j]), 0.5, 1.2, 0.15), T(1, 1.75 + j * B(0.25) * 0.8), 0.12, -0.6 + j * 0.2, 'dry', 0.3)
# T·03 DiXML — o túnel e as linhas
for j in range(8):
    M.add(whoosh(0.18, 800 + j * 500, 5000, 1.2, 0.3), T(2, 0.2 + j * 0.14), 0.07, -0.4 + j * 0.1)
for j in range(12):
    M.add(thock(260 + j * 12), T(2, 1.45 + j * B(0.25) * 0.8), 0.1, 0.3)
M.add(zipper(0.18, 3000, 300), T(2, 1.65), 0.08)
ticks(T(2, 1.8), T(2, 2.65), 44, 0.018, 4200)
# T·04 GerarPendentes — a esteira
for k in range(70):
    M.add(click(1800 + G.uniform(-200, 600), 0.012), T(3, 0.55 + k * 0.028), 0.028, G.uniform(-0.6, 0.6))
M.add(pluck(midi(76), 0.8, 1.0, 0.3), T(3, 2.2), 0.14, 0.4, 'dry', 0.4)
# T·05 GerarServPend — quatro peneiras
for w, t0 in enumerate((0.45, 0.92, 1.39, 1.86)):
    M.add(zipper(0.22, 2600 - w * 300, 400), T(4, t0), 0.08, -0.5 + w * 0.33)
    M.add(pluck(midi((72, 74, 76, 71)[w]), 0.6, 1.2, 0.2), T(4, t0 + 0.28), 0.14, -0.3 + w * 0.2, 'dry', 0.3)
M.add(blip_down(700, 180, 0.12), T(4, 2.3), 0.14)
# T·06 Base de conhecimento — medidores e células
for j in range(3):
    ratchet(T(5, 0.35 + j * 0.1), T(5, 1.35 + j * 0.1), 60, 20, 0.02, -0.5 + j * 0.5, 5200)
for j in range(10):
    M.add(pluck(midi((79, 81, 83, 86, 88)[j % 5]), 0.4, 1.0, 0.12), T(5, 1.15 + j * B(0.25) * 0.85), 0.08, -0.4 + j * 0.08, 'dry', 0.3)
# T·07 Resumo Executivo — rosca, barras, conferência
M.add(whoosh(1.0, 400, 2600, 0.8, 0.6, 'pink'), T(6, 0.3), 0.1, np.linspace(-0.5, 0.5, n_of(1.0)))
for j in range(12):
    M.add(thock(180 + j * 20), T(6, 0.6 + (j // 3) * 0.08 + (j % 3) * 0.12), 0.07, -0.3 + (j // 3) * 0.2)
for j in range(6):
    M.add(pluck(midi(81 + (0, 3, 5, 7, 10, 12)[j]), 0.5, 1.2, 0.15), T(6, 1.5 + j * B(0.25) * 0.8), 0.12, -0.5 + j * 0.2, 'dry', 0.3)
# T·08 Faturabot — o caminhão, a balança, o carimbo
nr = n_of(1.0)
rum = filt(noise(nr), 'lp', 180) * 2 + filt(saw(logline(55, 38, nr), nr), 'lp', 300) * 0.5
M.add(rum * ar(nr, 0.2, 0.3), T(7, 0.0), 0.2, np.linspace(-0.8, 0.1, nr))
M.add(filt(noise(n_of(0.35)), 'hp', 3000) * ar(n_of(0.35), 0.01, 0.25), T(7, 0.82), 0.05, 0.1)
ratchet(T(7, 0.9), T(7, 1.35), 70, 25, 0.03, 0.3)
ratchet(T(7, 1.2), T(7, 1.6), 70, 25, 0.03, 0.4)
M.add(sine(logline(600, 1600, n_of(0.12)), n_of(0.12)) * env(n_of(0.12), 0.003, 0.06), T(7, 1.62), 0.06)
M.add(thock(110), T(7, B(4)), 0.5, 0, 'dry', 0.2)
M.add(boom(100, 45, 0.6, 0.16), T(7, B(4)), 0.26)
M.add(clap(), T(7, B(4)), 0.3, 0, 'dry', 0.3)
chord([64, 67, 71, 74], T(7, B(4)) + 0.05, 0.11)
M.add(whoosh(0.5, 300, 5000, 0.9, 0.9), B(72) - 0.5, 0.2)

# ================= compassos 19–20 · FLUXO =================
for k in range(8):
    M.add(pluck(midi(PLANET[k]), 0.8, 1.0, 0.25), B(72) + 0.1 + k * B(0.25), 0.16, PAN8[k], 'dry', 0.35)
ARP = [69, 72, 76, 79, 81, 79, 76, 72]
for i in range(40):
    ta = B(73.5) + i * B(0.125)
    if ta > B(78.4):
        break
    M.add(pluck(midi(ARP[i % 8] + 12), 0.3, 0.9, 0.1), ta, 0.045, 0.5 * np.sin(i * 1.1), 'dry', 0.4)
M.add(whoosh(0.7, 600, 2800, 0.9, 0.5, 'pink'), B(74), 0.08)
M.add(riser(B(1.4), 180, 2000, 1.0), B(78.6), 0.28)
M.add(whoosh(B(1.4), 5000, 300, 0.8, 0.9), B(78.6), 0.18)

# ================= compassos 21–22 · NÚMEROS =================
for k, b in enumerate((80, 82, 84, 86)):
    M.add(kick(170, 40, 0.5, 0.9), B(b), 0.85, 0, 'drums')
    M.add(boom(80 - k * 5, 34, 1.0, 0.3), B(b), 0.3)
    M.add(crash(1.0, 0.3), B(b), 0.07, 0, 'dry', 0.3)
    ratchet(B(b), B(b) + 0.55, 80, 18, 0.03, 0.2)
    chord([[57, 64, 67, 72], [53, 60, 64, 69], [55, 62, 67, 71], [52, 59, 64, 67]][k], B(b), 0.1)
    M.add(kick(), B(b + 1), 0.6, 0, 'drums')
    if b < 86:
        M.add(whoosh(0.3, 5000, 400, 1.0, 0.3), B(b + 2) - 0.12, 0.12)
pad([57, 64, 67, 71, 72], B(80), B(8), 0.13, 800, 3600, 'dry', 0.4, 0.05, 0.3)
M.add(sub(midi(33), B(7.5), 0.02, 0.2, 2.0), B(80), 0.14)
M.add(riser(B(1.6), 150, 1600, 1.0), B(86.4), 0.26)

# ================= compassos 23–24 · ASSINATURA =================
M.add(boom(55, 30, 2.6, 0.9), B(88), 0.3, 0, 'dry', 0.25)
M.add(crash(2.4, 0.9), B(88), 0.1, 0, 'dry', 0.4)
pad([53, 57, 60, 64, 67], B(88), B(4) + 0.1, 0.22, 900, 4200, 'dry', 0.5, 0.2, 0.2)      # Fmaj9
pad([48, 55, 60, 62, 64, 67], B(92), B(4) - 0.1, 0.22, 4200, 1500, 'dry', 0.5, 0.05, 0.6)  # Cadd9
M.add(sub(midi(29), B(4), 0.3, 0.1, 2.2), B(88), 0.2)
M.add(sub(midi(24), B(4), 0.05, 0.5, 2.0), B(92), 0.22)
for i, m in enumerate((84, 88, 91)):                    # os três nascem
    M.add(fm_bell(midi(m), 2.6, 3.5, 1.3, 1.6), B(88.6) + i * B(0.33), 0.07, (-0.3, 0, 0.3)[i], 'dry', 0.7)
ARP2 = [65, 69, 72, 76, 77, 76, 72, 69]
for i in range(14):
    M.add(pluck(midi(ARP2[i % 8] + 12), 0.5, 0.8, 0.18), B(89) + i * B(0.25), 0.06, 0.5 * np.sin(i * 1.3), 'dry', 0.55)
for tb in (B(89), B(90)):
    M.add(whoosh(0.4, 700, 2600, 0.8, 0.5, 'pink'), tb - 0.05, 0.07)
M.add(kick(170, 40, 0.6, 0.9), B(92), 0.8, 0, 'drums')
M.add(boom(70, 28, 2.2, 0.8), B(92), 0.36)
M.add(whoosh(0.6, 400, 5200, 1.0, 0.7), B(92), 0.2, np.linspace(-0.6, 0.2, n_of(0.6)))
chord([60, 64, 67, 71, 74], B(92.6), 0.12, step=0.04)
M.add(whoosh(B(1.4), 600, 3000, 0.9, 0.5), B(93), 0.08, np.linspace(-0.7, 0.7, n_of(B(1.4))))
ticks(B(94), B(94) + 0.5, 30, 0.012, 5200)
for i, m in enumerate((72, 76, 79)):                    # a marca pulsa: três notas, agora em maior
    M.add(pluck(midi(m), 1.4, 1.1, 0.55), B(95) + i * B(0.25), 0.26, (-0.2, 0.1, 0.25)[i], 'dry', 0.5)
    M.add(fm_bell(midi(m + 12), 1.2, 3.5, 0.9, 0.7), B(95) + i * B(0.25), 0.05, 0, 'dry', 0.6)

# ================= mixagem =================
kt = np.array([B(b) for b in KICKS + [80, 82, 84, 86, 92]])
t = tt(M.N)
duck = np.ones(M.N)
for k in kt:
    m = (t >= k) & (t < k + 0.6)
    duck[m] = np.minimum(duck[m], 1 - 0.66 * np.exp(-(t[m] - k) / 0.11))
music = M.bus['pump'] * duck + M.bus['drums']
irL, irR = reverb_ir(2.4)
v = M.bus['verb']
wet = np.vstack([signal.fftconvolve(v[0], irL)[:M.N], signal.fftconvolve(v[1], irR)[:M.N]])
sec = 1 + 0.3 * (1 - np.clip((t - 7.4) / 0.2, 0, 1)) + 0.3 * np.clip((t - 41.3) / 0.3, 0, 1)
mix = M.bus['dry'] * sec + music + wet * 0.5 * sec
mix = np.vstack([filt(mix[0], 'hp', 24), filt(mix[1], 'hp', 24)])
mix /= np.max(np.abs(mix)) + 1e-9


def lufs(x):
    """loudness integrada BS.1770 (ponderação K, blocos de 400 ms, gates)"""
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1, -1.99004745483398, 0.99007225036621]
    k = signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=1), axis=1)
    blk, hop = n_of(0.4), n_of(0.1)
    ms = np.array([np.sum(np.mean(k[:, i:i + blk] ** 2, axis=1)) for i in range(0, k.shape[1] - blk, hop)])
    ld = -0.691 + 10 * np.log10(ms + 1e-12)
    g = ms[ld > -70]
    rel = -0.691 + 10 * np.log10(np.mean(g)) - 10
    return -0.691 + 10 * np.log10(np.mean(ms[(ld > -70) & (ld > rel)]))


def limiter(x, ceil=0.84, look=0.003, rel=0.09):
    """limitador com antecipação: o ganho desce antes do pico e volta devagar"""
    from scipy.ndimage import maximum_filter1d
    L = n_of(look)
    pk = maximum_filter1d(np.abs(x).max(0), size=2 * L + 1)
    g = np.minimum(1.0, ceil / np.maximum(pk, 1e-9))
    a = np.exp(-1 / (rel * SR))
    out = np.empty_like(g)
    cur = 1.0
    for i in range(len(g)):
        cur = g[i] if g[i] < cur else a * cur + (1 - a) * g[i]
        out[i] = cur
    return x * out


for _ in range(3):                                      # mira −14 LUFS com teto de −1 dBFS
    mix = mix * 10 ** ((-14.0 - lufs(mix)) / 20)
    mix = limiter(mix)
fade = np.ones(M.N)
fi = t >= 44.4
fade[fi] = np.cos(np.clip((t[fi] - 44.4) / 0.6, 0, 1) * np.pi / 2) ** 2
fade[:n_of(0.004)] = np.linspace(0, 1, n_of(0.004))
mix = mix * fade
print('LUFS', round(lufs(mix), 2))

out = sys.argv[1] if len(sys.argv) > 1 else 'soundtrack.wav'
pcm = np.clip(np.round(mix.T * 8388607), -8388608, 8388607).astype(np.int32)
b = (pcm.reshape(-1, 1).view(np.uint8).reshape(-1, 4)[:, :3]).tobytes()
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(3)
    w.setframerate(SR)
    w.writeframes(b)
print('wrote', out, f'{M.N / SR:.3f}s', 'peak', float(np.max(np.abs(mix))))
