from Util.map_functions import *

def generate_map_with_curvature_like(M):
    # FFT
    F = np.fft.fft2(M)

    # Magnitude and phase
    mag = np.abs(F)
    phase = np.angle(F)

    # Randomize phase (except DC component)
    random_phase = np.random.uniform(-np.pi, np.pi, size=M.shape)
    random_phase[0, 0] = phase[0, 0]  # preserve mean

    # Recombine
    F_new = mag * np.exp(1j * random_phase)

    # Inverse FFT
    M_new = np.real(np.fft.ifft2(F_new))

    # Normalize back to [0, 1]
    M_new -= M_new.min()
    M_new /= M_new.max()

    # Match mean exactly
    M_new += M.mean() - M_new.mean()

    return np.clip(M_new, 0, 1)


def generate_n_maps(n):
    map_apriori = get_map()
    PIXEL_WIDTH[0] = PIXEL_WIDTH_CARMEL[0]
    map_apriori = discretization(map_apriori, 2, by_max=False)
    for i in range(n):
        rand_map = generate_map_with_curvature_like(map_apriori)
        plt.gray()
        plt.imshow(rand_map)
        plt.savefig(f"../maps/high_res_BDIKA/high res map {i}")
        np.save(f"../maps/high_res_BDIKA/high_res_map_{i}", rand_map)
        plt.clf()


generate_n_maps(70)