import numpy as np
import numpy.fft as fft
import s2fft.sampling as samples
import s2fft.wigner as wigner


def inverse_direct(
    flm: np.ndarray, L: int, spin: int = 0, sampling: str = "mw"
) -> np.ndarray:

    # TODO: Check flm shape consistent with L

    ntheta = samples.ntheta(L, sampling)
    nphi = samples.nphi_equiang(L, sampling)
    f = np.zeros((ntheta, nphi), dtype=np.complex128)

    thetas = samples.thetas(L, sampling)
    phis_equiang = samples.phis_equiang(L, sampling)

    dl = np.zeros((2 * L - 1, 2 * L - 1), dtype=np.float64)

    for t, theta in enumerate(thetas):

        for el in range(0, L):

            dl = wigner.risbo.compute_full(dl, theta, L, el)

            if el >= np.abs(spin):

                elfactor = np.sqrt((2 * el + 1) / (4 * np.pi))

                for m in range(-el, el + 1):

                    i = samples.elm2ind(el, m)

                    for p, phi in enumerate(phis_equiang):

                        f[t, p] += (
                            (-1) ** spin
                            * elfactor
                            * np.exp(1j * m * phi)
                            * dl[m + L - 1, -spin + L - 1]
                            * flm[i]
                        )

    return f


def inverse_sov(
    flm: np.ndarray, L: int, spin: int = 0, sampling: str = "mw"
) -> np.ndarray:

    # TODO: Check flm shape consistent with L

    ntheta = samples.ntheta(L, sampling)
    nphi = samples.nphi_equiang(L, sampling)
    f = np.zeros((ntheta, nphi), dtype=np.complex128)

    thetas = samples.thetas(L, sampling)
    phis_equiang = samples.phis_equiang(L, sampling)

    dl = np.zeros((2 * L - 1, 2 * L - 1), dtype=np.float64)

    fmt = np.zeros((2 * L - 1, ntheta), dtype=np.complex128)
    for t, theta in enumerate(thetas):

        for el in range(0, L):

            dl = wigner.risbo.compute_full(dl, theta, L, el)

            if el >= np.abs(spin):

                elfactor = np.sqrt((2 * el + 1) / (4 * np.pi))

                for m in range(-el, el + 1):

                    i = samples.elm2ind(el, m)

                    fmt[m + L - 1, t] += (
                        (-1) ** spin * elfactor * dl[m + L - 1, -spin + L - 1] * flm[i]
                    )

    for t, theta in enumerate(thetas):

        for p, phi in enumerate(phis_equiang):

            for m in range(-(L - 1), L):

                f[t, p] += fmt[m + L - 1, t] * np.exp(1j * m * phi)

    return f


def inverse_sov_fft(
    flm: np.ndarray, L: int, spin: int = 0, sampling: str = "mw"
) -> np.ndarray:

    # TODO: Check flm shape consistent with L

    ntheta = samples.ntheta(L, sampling)
    nphi = samples.nphi_equiang(L, sampling)
    f = np.zeros((ntheta, nphi), dtype=np.complex128)

    thetas = samples.thetas(L, sampling)
    phis_equiang = samples.phis_equiang(L, sampling)

    dl = np.zeros((2 * L - 1, 2 * L - 1), dtype=np.float64)

    fmt = np.zeros((2 * L - 1, ntheta), dtype=np.complex128)
    for t, theta in enumerate(thetas):

        for el in range(0, L):

            dl = wigner.risbo.compute_full(dl, theta, L, el)

            if el >= np.abs(spin):

                elfactor = np.sqrt((2 * el + 1) / (4 * np.pi))

                for m in range(-el, el + 1):

                    i = samples.elm2ind(el, m)

                    fmt[m + L - 1, t] += (
                        (-1) ** spin * elfactor * dl[m + L - 1, -spin + L - 1] * flm[i]
                    )

    fmt_shift = np.zeros((2 * L - 1, ntheta), dtype=np.complex128)
    for t, theta in enumerate(thetas):

        fmt_shift[0:L, t] = fmt[0 + L - 1 : L + L - 1, t]
        fmt_shift[L : 2 * L - 1, t] = fmt[-(L - 1) + L - 1 : 0 + L - 1, t]

        # f[t, :] = fft.ifft(fmt_shift[:, t], norm="forward")  # * 2 * np.pi / (2 * L - 1)

        # for p, phi in enumerate(phis_equiang):

        #     for m in range(-(L - 1), L):
        #         mp = m + L - 1

        #         # f[t, p] += fmt[m + L - 1, t] * np.exp(1j * m * phi)
        #         # f[t, p] += fmt_shift[m, t] * np.exp(1j * (mp - L + 1) * phi)
        #         # f[t, p] += (
        #         #     fmt_shift[m, t]
        #         #     * np.exp(1j * mp * phi)
        #         #     * np.exp(-1j * (L - 1) * phi)
        #         # )
        #         # f[t, p] += (
        #         #     fmt[mp, t] * np.exp(1j * mp * phi) * np.exp(-1j * (L - 1) * phi)
        #         # )
        #         f[t, p] += fmt_shift[mp, t] * np.exp(1j * mp * phi)

    # f = fft.ifft(fft.ifftshift(fmt, axes=0), axis=0, norm="forward")
    f = fft.ifft(fmt_shift, axis=0, norm="forward")
    f = np.transpose(f)

    return f


def forward_direct(
    f: np.ndarray, L: int, spin: int = 0, sampling: str = "mw"
) -> np.ndarray:

    # TODO: Check f shape consistent with L

    if sampling.lower() != "dh":

        raise ValueError(
            f"Sampling scheme sampling={sampling} not implement (only DH supported at present)"
        )

    ncoeff = samples.ncoeff(L)

    flm = np.zeros(ncoeff, dtype=np.complex128)

    thetas = samples.thetas(L, sampling)
    phis_equiang = samples.phis_equiang(L, sampling)

    dl = np.zeros((2 * L - 1, 2 * L - 1), dtype=np.float64)

    for t, theta in enumerate(thetas):

        weight = samples.weight_dh(theta, L) * 2 * np.pi / (2 * L - 1)

        for el in range(0, L):

            dl = wigner.risbo.compute_full(dl, theta, L, el)

            if el >= np.abs(spin):

                elfactor = np.sqrt((2 * el + 1) / (4 * np.pi))

                for m in range(-el, el + 1):

                    i = samples.elm2ind(el, m)

                    for p, phi in enumerate(phis_equiang):

                        flm[i] += (
                            weight
                            * (-1) ** spin
                            * elfactor
                            * np.exp(-1j * m * phi)
                            * dl[m + L - 1, -spin + L - 1]
                            * f[t, p]
                        )

    return flm
