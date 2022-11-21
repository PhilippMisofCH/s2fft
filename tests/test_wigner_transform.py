import pytest
import so3
import numpy as np
import s2fft.wigner.samples as samples
import s2fft.wigner.transform as transform


L_to_test = [8, 16]
N_to_test = [2, 4, 6]
sampling_schemes = ["mw", "mwss", "dh"]


@pytest.mark.parametrize("L", L_to_test)
@pytest.mark.parametrize("N", N_to_test)
@pytest.mark.parametrize("sampling", sampling_schemes)
def test_inverse_wigner_transform(flmn_generator, L: int, N: int, sampling: str):

    flmn_3D = flmn_generator(L=L, N=N, reality=False)
    flmn_1D = samples.flmn_3d_to_1d(flmn_3D, L, N)

    params = so3.create_parameter_dict(L=L, N=N)
    f_check = so3.inverse(flmn_1D, params)

    f = transform.inverse_wigner_transform(flmn_3D, L, N)
    f = np.moveaxis(f, -1, 0).flatten("C")

    np.testing.assert_allclose(f, f_check, atol=1e-14)


@pytest.mark.parametrize("L", L_to_test)
@pytest.mark.parametrize("N", N_to_test)
@pytest.mark.parametrize("sampling", sampling_schemes)
def test_forward_wigner_transform(flmn_generator, L: int, N: int, sampling: str):
    params = so3.create_parameter_dict(L=L, N=N)

    flmn_3D = flmn_generator(L=L, N=N, reality=False)
    flmn_1D = samples.flmn_3d_to_1d(flmn_3D, L, N)

    f_1D = so3.inverse(flmn_1D, params)
    f_3D = f_1D.reshape(
        samples._ngamma(N), samples._nbeta(L), samples._nalpha(L)
    )
    f_3D = np.moveaxis(f_3D, 0, -1)

    flmn_check = samples.flmn_1d_to_3d(so3.forward(f_1D, params), L, N)
    flmn = transform.forward_wigner_transform(f_3D, L, N)

    np.testing.assert_allclose(flmn, flmn_check, atol=1e-14)
