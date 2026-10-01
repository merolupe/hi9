"""Pequena caixa de ferramentas de síntese (numpy + scipy) para a trilha do reel.

Osciladores com anti-aliasing (PolyBLEP), biquads RBJ (inclusive varredura de
corte em blocos, com estado carregado), ruído, sino FM, reverb de convolução
sintética e um mixer estéreo com envio para o reverb.
"""
import numpy as np
from scipy import signal

SR = 48000
RNG = np.random.default_rng(20260925)


def n_of(d):
    return max(1, int(round(d * SR)))


def tt(n):
    return np.arange(n) / SR


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# ---------------- envelopes ----------------
def env(n, a=0.002, decay=0.3, hold=0.0):
    t = tt(n)
    e = np.clip(t / max(a, 1e-5), 0, 1)
    e = e * np.where(t < a + hold, 1.0, np.exp(-(t - a - hold) / decay))
    return e


def ar(n, a, r, curve=2.0):
    """ataque e relaxamento suaves (sem cliques), duração total n"""
    t = tt(n)
    d = n / SR
    up = np.clip(t / max(a, 1e-5), 0, 1) ** curve
    down = np.clip((d - t) / max(r, 1e-5), 0, 1) ** curve
    return up * down


# ---------------- osciladores ----------------
def phase(freq, n, ph0=0.0):
    f = np.full(n, float(freq)) if np.isscalar(freq) else np.asarray(freq, float)
    return (ph0 + np.cumsum(f) / SR) % 1.0, f / SR


def sine(freq, n, ph0=0.0):
    p, _ = phase(freq, n, ph0)
    return np.sin(2 * np.pi * p)


def saw(freq, n, ph0=None):
    p, dt = phase(freq, n, RNG.random() if ph0 is None else ph0)
    y = 2 * p - 1
    m = p < dt
    x = p[m] / dt[m]
    y[m] -= x + x - x * x - 1
    m = p > 1 - dt
    x = (p[m] - 1) / dt[m]
    y[m] -= x * x + x + x + 1
    return y


def tri(freq, n):
    p, _ = phase(freq, n)
    return 1 - 4 * np.abs(p - 0.5)


def noise(n):
    return RNG.standard_normal(n)


def pink(n):
    b, a = [0.049922035, -0.095993537, 0.050612699, -0.004408786], [1, -2.494956002, 2.017265875, -0.522189400]
    return signal.lfilter(b, a, noise(n)) * 4


# ---------------- filtros RBJ ----------------
def rbj(kind, fc, q=0.707, gain_db=0.0):
    w = 2 * np.pi * min(fc, SR * 0.45) / SR
    c, s = np.cos(w), np.sin(w)
    al = s / (2 * q)
    if kind == 'lp':
        b = [(1 - c) / 2, 1 - c, (1 - c) / 2]; a = [1 + al, -2 * c, 1 - al]
    elif kind == 'hp':
        b = [(1 + c) / 2, -(1 + c), (1 + c) / 2]; a = [1 + al, -2 * c, 1 - al]
    elif kind == 'bp':
        b = [al, 0, -al]; a = [1 + al, -2 * c, 1 - al]
    elif kind == 'peak':
        A = 10 ** (gain_db / 40)
        b = [1 + al * A, -2 * c, 1 - al * A]; a = [1 + al / A, -2 * c, 1 - al / A]
    else:
        raise ValueError(kind)
    b, a = np.array(b) / a[0], np.array(a) / a[0]
    return b, a


def filt(x, kind, fc, q=0.707, gain_db=0.0):
    b, a = rbj(kind, fc, q, gain_db)
    return signal.lfilter(b, a, x)


def sweep(x, kind, fc, q=0.707, block=128):
    """filtro com corte variável: fc é array do tamanho de x (ou escalar)"""
    fc = np.full(len(x), float(fc)) if np.isscalar(fc) else np.asarray(fc, float)
    y = np.zeros_like(x)
    zi = np.zeros(2)
    for i in range(0, len(x), block):
        b, a = rbj(kind, fc[min(i + block // 2, len(x) - 1)], q)
        y[i:i + block], zi = signal.lfilter(b, a, x[i:i + block], zi=zi)
    return y


def logline(f0, f1, n, curve=1.0):
    u = np.linspace(0, 1, n) ** curve
    return np.exp(np.log(f0) + (np.log(f1) - np.log(f0)) * u)


# ---------------- vozes ----------------
def fm_bell(freq, d, ratio=3.5, index=2.4, decay=1.1):
    n = n_of(d)
    t = tt(n)
    idx = index * np.exp(-t / (decay * 0.35))
    mod = np.sin(2 * np.pi * freq * ratio * t) * idx
    car = np.sin(2 * np.pi * freq * t + mod)
    return car * env(n, 0.001, decay)


def pluck(freq, d=0.7, bright=1.0, decay=0.22):
    n = n_of(d)
    t = tt(n)
    idx = 1.6 * bright * np.exp(-t / 0.05)
    mod = np.sin(2 * np.pi * freq * 2 * t) * idx
    y = np.sin(2 * np.pi * freq * t + mod) * 0.8 + tri(freq * 2, n) * 0.12 * np.exp(-t / 0.04)
    return y * env(n, 0.0015, decay)


def supersaw(freqs, d, voices=5, detune=0.11):
    n = n_of(d)
    y = np.zeros(n)
    for f in freqs:
        for v in range(voices):
            cents = (v - (voices - 1) / 2) / ((voices - 1) / 2) * detune * 100 if voices > 1 else 0
            y += saw(f * 2 ** (cents / 1200), n)
    return y / (len(freqs) * voices) ** 0.5


# ---------------- espaço ----------------
def reverb_ir(rt60=2.3, pre=0.018, seed=3):
    g = np.random.default_rng(seed)
    n = n_of(rt60 * 1.1)
    t = tt(n)
    decay = np.exp(-6.91 * t / rt60)
    out = []
    for _ in range(2):
        x = g.standard_normal(n) * decay
        x = filt(x, 'lp', 7000)
        x = filt(x, 'hp', 180)
        x = np.concatenate([np.zeros(n_of(pre)), x])
        out.append(x / np.sqrt(np.sum(x ** 2)))
    return out


def pan_gains(p):
    p = np.clip(p, -1, 1)
    return np.cos((p + 1) * np.pi / 4), np.sin((p + 1) * np.pi / 4)


class Mix:
    """barramentos estéreo: dry, verb (envio) e pump (sidechain do bumbo)"""

    def __init__(self, dur):
        self.N = n_of(dur)
        self.bus = {k: np.zeros((2, self.N)) for k in ('dry', 'pump', 'drums', 'verb')}

    def add(self, x, t0, gain=1.0, pan=0.0, bus='dry', send=0.0):
        i0 = int(round(t0 * SR))
        if i0 >= self.N:
            return
        x = np.asarray(x, float)
        if x.ndim == 1:
            L = len(x)
            gl, gr = pan_gains(pan if np.isscalar(pan) else np.asarray(pan)[:L])
            st = np.vstack([x * gl, x * gr])
        else:
            st = x
        s0 = max(0, -i0)
        i0 = max(0, i0)
        L = min(st.shape[1] - s0, self.N - i0)
        if L <= 0:
            return
        self.bus[bus][:, i0:i0 + L] += st[:, s0:s0 + L] * gain
        if send > 0:
            self.bus['verb'][:, i0:i0 + L] += st[:, s0:s0 + L] * gain * send
