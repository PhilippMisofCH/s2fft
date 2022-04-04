from re import I
import numpy as np


def compute_full(beta: float, el: int, L: int) -> np.ndarray:
    """Constructs the Wigner-d matrix via Turok recursion

    Args:

        beta (float): polar angle in radians
        el (int): Angular bandlimit of wigner-d matrix
        L (int): Angular bandlimit of overall transform

    Raises:

        ValueError: If el is greater than L

    Returns:

        Wigner-d matrix of dimension [2*L-1, 2*L-1]
    """
    if el >= L:
        raise ValueError(
            f"Wigner-d bandlimit {el} cannot be equal to or greater than L={L}"
        )

    dl = np.zeros((2 * L - 1, 2 * L - 1), dtype=np.float64)
    dl[L - 1 - el : L + el, L - 1 - el : L + el] = turok_fill(
        turok_quarter(beta, el), el
    )
    return dl


def compute_spin_slice(
    beta: float, el: int, L: int, spin: int, accelerate: bool = False
) -> np.ndarray:
    """Constructs the Wigner-d matrix via Turok recursion

    TODO: Fix reflection optimisations

    Args:

        beta (float): polar angle in radians
        el (int): Angular bandlimit of wigner-d matrix
        L (int): Angular bandlimit of overall transform
        spin (int): m' at which to slice matrix
        accelerate (bool): optimise indexing to minimise reflections

    Raises:

        ValueError: If el is greater than L
        ValueError: If el is less than spin
        ValueError: If reflection acceleration is activated

    Returns:

        Wigner-d matrix of dimension [2*L-1]
    """
    if el < spin:
        raise ValueError(f"Wigner-D not valid for l={el} < spin={spin}.")

    if accelerate == True:
        raise ValueError(f"Reflection acceleration scheme not yet stable.")

    if el >= L:
        raise ValueError(
            f"Wigner-d bandlimit {el} cannot be equal to or greater than L={L}"
        )

    dl = np.zeros(2 * L - 1, dtype=np.float64)
    dl[L - 1 - el : L + el] = turok_quarter_spin(beta, el, spin, accelerate)

    return dl


def turok_quarter_spin(
    beta: float, l: int, spin: int, accelerate: bool = False
) -> np.ndarray:
    """Evaluates the left quarter triangle of the Wigner-d matrix via
        Turok recursion at ONLY a specific spin index

    TODO: Fix reflection optimisations

    Args:
        beta (float): polar angle in radians
        l (int): angular bandlimit
        spin (int): spin indice to evaluate
        accelerate (bool): optimise indexing to minimise reflections

    Returns:

        Wigner-d matrix of dimension [2*L-1] with
        left quarter triangle populated only at m' = spin
    """
    # Analytically evaluate singularities
    if np.abs(beta) <= 0:
        dl = np.zeros(2 * l + 1, dtype=np.float64)
        dl[l - spin] = 1
        return dl

    if np.abs(beta) >= np.pi:
        dl = np.zeros(2 * l + 1, dtype=np.float64)
        dl[l + spin] = (-1) ** (l + spin)
        return dl

    if l == 0:
        return 1

    # Define constants adopted throughout
    dl = np.zeros((2 * l + 1, 2 * l + 1), dtype=np.float64)
    lp1 = 1  # Offset for indexing (currently -l <= m <= l)

    # These constants handle overflow by retrospectively renormalising
    big_const = 1e10
    bigi = 1.0 / big_const
    lbig = np.log(big_const)

    # Trigonometric constant adopted throughout
    c = np.cos(beta)
    s = np.sin(beta)
    t = np.tan(-beta / 2.0)
    c2 = np.cos(beta / 2.0)
    omc = 1.0 - c

    # Vectors with indexing -L < m < L adopted throughout
    lrenorm = np.zeros(2 * l + 1, dtype=np.float64)
    cpi = np.zeros(2 * l + 1, dtype=np.float64)
    cp2 = np.zeros(2 * l + 1, dtype=np.float64)
    log_first_row = np.zeros(2 * l + 1, dtype=np.float64)
    sign = np.zeros(2 * l + 1, dtype=np.float64)

    # Populate vectors for first row
    log_first_row[0] = 2.0 * l * np.log(np.abs(c2))
    sign[0] = 1.0

    for i in range(2, 2 * l + 2):
        m = l + 1 - i
        ratio = np.sqrt((m + l + 1) / (l - m))
        log_first_row[i - 1] = log_first_row[i - 2] + np.log(ratio) + np.log(np.abs(t))
        sign[i - 1] = sign[i - 2] * t / np.abs(t)

    # Initialising coefficients cp(m)= cplus(l-m).
    for m in range(1, l + 2):
        xm = l - m
        cpi[m - 1] = 2.0 / np.sqrt(l * (l + 1) - xm * (xm + 1))

    for m in range(2, l + 2):
        cp2[m - 1] = cpi[m - 1] / cpi[m - 2]

    dl[1 - lp1, 1 - lp1] = 1.0
    dl[2 * l + 1 - lp1, 1 - lp1] = 1.0

    # Use Turok recursion to fill from diagonal to horizontal (lower left eight)
    index = l - spin + lp1
    m_cap = l - np.abs(spin) + lp1

    for i in range(l - np.abs(spin) + lp1, l + 2):
        dl[i - lp1, 1 - lp1] = 1.0
        lamb = ((l + 1) * omc - i + c) / s
        dl[i - lp1, 2 - lp1] = lamb * dl[i - lp1, 1 - lp1] * cpi[0]

        if i > 2:
            for m in range(2, i):
                lamb = ((l + 1) * omc - i + m * c) / s
                dl[i - lp1, m + 1 - lp1] = (
                    lamb * cpi[m - 1] * dl[i - lp1, m - lp1]
                    - cp2[m - 1] * dl[i - lp1, m - 1 - lp1]
                )

                if dl[i - lp1, m + 1 - lp1] > big_const:
                    lrenorm[i - 1] = lrenorm[i - 1] - lbig
                    for im in range(1, m + 2):
                        dl[i - lp1, im - lp1] = dl[i - lp1, im - lp1] * bigi

    for i in range(l + 2, l + np.abs(spin) + 2):
        dl[i - lp1, 1 - lp1] = 1.0
        lamb = ((l + 1) * omc - i + c) / s
        dl[i - lp1, 2 - lp1] = lamb * dl[i - lp1, 1 - lp1] * cpi[0]

        if i < 2 * l:
            for m in range(2, 2 * l - i + 2):
                lamb = ((l + 1) * omc - i + m * c) / s
                dl[i - lp1, m + 1 - lp1] = (
                    lamb * cpi[m - 1] * dl[i - lp1, m - lp1]
                    - cp2[m - 1] * dl[i - lp1, m - 1 - lp1]
                )

                if dl[i - lp1, m + 1 - lp1] > big_const:
                    lrenorm[i - 1] = lrenorm[i - 1] - lbig
                    for im in range(1, m + 2):
                        dl[i - lp1, im - lp1] = dl[i - lp1, im - lp1] * bigi

    # Apply renormalisation
    for i in range(l - np.abs(spin) + lp1, l + 2):
        renorm = sign[i - 1] * np.exp(log_first_row[i - 1] - lrenorm[i - 1])
        for j in range(1, i + 1):
            dl[i - lp1, j - lp1] = dl[i - lp1, j - lp1] * renorm

    for i in range(l + 2, l + np.abs(spin) + 2):
        renorm = sign[i - 1] * np.exp(log_first_row[i - 1] - lrenorm[i - 1])
        for j in range(1, 2 * l + 2 - i + 1):
            dl[i - lp1, j - lp1] = dl[i - lp1, j - lp1] * renorm

    if accelerate == True:
        # Reflect across diagonal
        if spin >= 0:
            for i in range(index, index + 1):
                sgn = -1
                for j in range(i + 1, l + 2):
                    dl[i - lp1, j - lp1] = dl[j - lp1, i - lp1] * sgn
                    sgn = sgn * (-1)

        # Reflect across anti-diagonal
        if spin < 0:
            for i in range(l + spin + 1, l + spin + 2):
                for j in range(l + 1, 2 * l + 1 - i + 1):
                    dl[2 * l + 2 - i - lp1, 2 * l + 2 - j - lp1] = dl[j - lp1, i - lp1]

        # Conjugate reflect across vertical line from spin to -spin
        for i in range(m_cap):
            dl[index - lp1, 2 * l - i] = (-1) ** (spin + i + 1) * dl[l + spin, i]

        if np.abs(spin) > 0:
            if spin >= 0:
                step = 1
                for i in range(m_cap, l):
                    dl[index - lp1, 2 * l - i] = (-1) ** (spin + i + 1) * dl[
                        l + spin - step, m_cap - 1
                    ]
                    step += 1
            else:
                step = 2 * np.abs(spin) - 1
                for i in range(m_cap, l):
                    dl[index - lp1, 2 * l - i] = dl[l - spin - step, m_cap - 1]
                    step -= 1
    else:
        dl = turok_fill(dl, l)

    return dl[index - lp1]


def turok_quarter(beta: float, l: int) -> np.ndarray:
    """Evaluates the left quarter triangle of the Wigner-d matrix via
        Turok recursion

    Args:
        dl (np.ndarray): Wigner-d matrix to populate
        beta (float): polar angle in radians
        l (int): Angular bandlimit

    Returns:

        Wigner-d matrix of dimension [2*L-1, 2*L-1] with
        left quarter triangle populated.
    """
    # Analytically evaluate singularities
    if np.abs(beta) <= 0:
        return np.identity(2 * l + 1, dtype=np.float64)

    if np.abs(beta) >= np.pi:
        dl = np.zeros((2 * l + 1, 2 * l + 1), dtype=np.float64)
        for m in range(-l, l + 1):
            dl[l - m, l + m] = (-1) ** (l + m)
        return dl

    if l == 0:
        return 1

    # Define constants adopted throughout
    dl = np.zeros((2 * l + 1, 2 * l + 1), dtype=np.float64)
    lp1 = 1  # Offset for indexing (currently -L < m < L in 2D)

    # These constants handle overflow by retrospectively renormalising
    big_const = 1e10
    big = big_const
    bigi = 1.0 / big_const
    lbig = np.log(big)

    # Trigonometric constant adopted throughout
    c = np.cos(beta)
    s = np.sin(beta)
    t = np.tan(-beta / 2.0)
    c2 = np.cos(beta / 2.0)
    omc = 1.0 - c

    # Vectors with indexing -L < m < L adopted throughout
    lrenorm = np.zeros(2 * l + 1, dtype=np.float64)
    cp = np.zeros(2 * l + 1, dtype=np.float64)
    cpi = np.zeros(2 * l + 1, dtype=np.float64)
    cp2 = np.zeros(2 * l + 1, dtype=np.float64)
    log_first_row = np.zeros(2 * l + 1, dtype=np.float64)
    sign = np.zeros(2 * l + 1, dtype=np.float64)

    # Populate vectors for first row
    log_first_row[0] = 2.0 * l * np.log(np.abs(c2))
    sign[0] = 1.0

    for i in range(2, 2 * l + 2):
        m = l + 1 - i
        ratio = np.sqrt((m + l + 1) / (l - m))
        log_first_row[i - 1] = log_first_row[i - 2] + np.log(ratio) + np.log(np.abs(t))
        sign[i - 1] = sign[i - 2] * t / np.abs(t)

    # Initialising coefficients cp(m)= cplus(l-m).
    for m in range(1, l + 2):
        xm = l - m
        cpi[m - 1] = 2.0 / np.sqrt(l * (l + 1) - xm * (xm + 1))
        cp[m - 1] = 1.0 / cpi[m - 1]

    for m in range(2, l + 2):
        cp2[m - 1] = cpi[m - 1] * cp[m - 2]

    dl[1 - lp1, 1 - lp1] = 1.0
    dl[2 * l + 1 - lp1, 1 - lp1] = 1.0

    # Use Turok recursion to fill from diagonal to horizontal (lower left eight)
    for index in range(2, l + 2):
        dl[index - lp1, 1 - lp1] = 1.0
        lamb = ((l + 1) * omc - index + c) / s
        dl[index - lp1, 2 - lp1] = lamb * dl[index - lp1, 1 - lp1] * cpi[0]
        if index > 2:
            for m in range(2, index):
                lamb = ((l + 1) * omc - index + m * c) / s
                dl[index - lp1, m + 1 - lp1] = (
                    lamb * cpi[m - 1] * dl[index - lp1, m - lp1]
                    - cp2[m - 1] * dl[index - lp1, m - 1 - lp1]
                )

                if dl[index - lp1, m + 1 - lp1] > big:
                    lrenorm[index - 1] = lrenorm[index - 1] - lbig
                    for im in range(1, m + 2):
                        dl[index - lp1, im - lp1] = dl[index - lp1, im - lp1] * bigi

    # Use Turok recursion to fill horizontal to anti-diagonal (upper left eight)
    for index in range(l + 2, 2 * l + 1):
        dl[index - lp1, 1 - lp1] = 1.0
        lamb = ((l + 1) * omc - index + c) / s
        dl[index - lp1, 2 - lp1] = lamb * dl[index - lp1, 1 - lp1] * cpi[0]
        if index < 2 * l:
            for m in range(2, 2 * l - index + 2):
                lamb = ((l + 1) * omc - index + m * c) / s
                dl[index - lp1, m + 1 - lp1] = (
                    lamb * cpi[m - 1] * dl[index - lp1, m - lp1]
                    - cp2[m - 1] * dl[index - lp1, m - 1 - lp1]
                )
                if dl[index - lp1, m + 1 - lp1] > big:
                    lrenorm[index - 1] = lrenorm[index - 1] - lbig
                    for im in range(1, m + 2):
                        dl[index - lp1, im - lp1] = dl[index - lp1, im - lp1] * bigi

    # Apply renormalisation
    for i in range(1, l + 2):
        renorm = sign[i - 1] * np.exp(log_first_row[i - 1] - lrenorm[i - 1])
        for j in range(1, i + 1):
            dl[i - lp1, j - lp1] = dl[i - lp1, j - lp1] * renorm

    for i in range(l + 2, 2 * l + 2):
        renorm = sign[i - 1] * np.exp(log_first_row[i - 1] - lrenorm[i - 1])
        for j in range(1, 2 * l + 2 - i + 1):
            dl[i - lp1, j - lp1] = dl[i - lp1, j - lp1] * renorm

    return dl


def turok_fill(dl: np.ndarray, l: int) -> np.ndarray:
    """Reflects Turok Wigner-d quarter plane to complete matrix

    Args:
        dl (np.ndarray): Wigner-d matrix to populate
        l (int): Angular bandlimit - 1 (conventions)

    Returns:

        Complete Wigner-d matrix of dimension [2*L-1, 2*L-1]
    """
    lp1 = 1  # Offset for indexing (currently -L < m < L in 2D)

    # Reflect across anti-diagonal
    for i in range(1, l + 1):
        for j in range(l + 1, 2 * l + 1 - i + 1):
            dl[2 * l + 2 - i - lp1, 2 * l + 2 - j - lp1] = dl[j - lp1, i - lp1]

    # Reflect across diagonal
    for i in range(1, l + 2):
        sgn = -1
        for j in range(i + 1, l + 2):
            dl[i - lp1, j - lp1] = dl[j - lp1, i - lp1] * sgn
            sgn = sgn * (-1)

    # Fill right matrix
    for i in range(l + 2, 2 * l + 2):
        sgn = (-1) ** (i + 1)
        for j in range(1, 2 * l + 2 - i + 1):
            dl[j - lp1, i - lp1] = dl[i - lp1, j - lp1] * sgn
            sgn = sgn * (-1)

        for j in range(i, 2 * l + 2):
            dl[j - lp1, i - lp1] = dl[2 * l + 2 - i - lp1, 2 * l + 2 - j - lp1]

    for i in range(l + 2, 2 * l + 2):
        for j in range(2 * l + 3 - i, i - 1 + 1):
            dl[j - lp1, i - lp1] = dl[2 * l + 2 - i - lp1, 2 * l + 2 - j - lp1]

    return dl
