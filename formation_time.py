from halo_mass_function import *
from scipy.integrate import quad
import matplotlib.pyplot as plt


def upcrossing(M1, M2, z1, z2, sig8=sigma8, h=h, kmax=30, window='TopHat', prec=1000, om0=om,
               ol0=oml, omb=omb, camb=False):
    w1 = delta_c(z1, om0, ol0)
    w2 = delta_c(z2, om0, ol0)
    S1 = sigma(M1, sig8, h, kmax, window, 'M', prec, om0, ol0, omb, camb) ** 2
    S2 = sigma(M2, sig8, h, kmax, window, 'M', prec, om0, ol0, omb, camb) ** 2
    dw = w1 - w2
    dS = S1 - S2
    return np.exp(-dw ** 2 / (2 * dS)) * dw / np.sqrt(2 * np.pi * dS ** 3)


def formation_time(M2, z1, z2, sig8=sigma8, h=h, kmax=30, window='TopHat', prec=1000, acc=np.int(1e4), om0=om,
                   ol0=oml, omb=omb, camb=False):
    # Mass = np.logspace(np.log10(M2/2), np.log10(M2), acc)
    Mass = np.linspace(M2 / 2, M2, acc)
    sigs = sigma(Mass, sig8, h, kmax, window, 'M', prec, om0, ol0, omb, camb) ** 2

    # M1 = np.sqrt(Mass[2:]*Mass[:-2])
    M1 = (Mass[2:] + Mass[:-2]) / 2
    dsig = -(sigs[2:] - sigs[:-2])
    fS = upcrossing(M1, M2, z1, z2, sig8, h, kmax, window, prec, om0, ol0, omb, camb)

    return M2 * np.sum(fS * dsig / M1)


'''def test(S1, S2):
    ds = 2*(S1-S2)
    return 1/np.sqrt(np.pi*ds)
M2 = 1e14
Mh = M2/2
masses = np.linspace(Mh, 0.999*M2, 10000)
sigs = sigma(masses, prec=100)**2
S2 = sigma(M2)**2
dsig = -sigs[1]+sigs[0]
te = test(sigs, S2)
res = M2*dsig*np.sum(te/masses)'''


def K(ds, dw, model='sheth', A=0.27, a=0.707, p=0.3):
    if model == 'sheth':
        ndw = np.sqrt(a) * dw
        return A * (1 + (ds / ndw ** 2) ** p) * ndw * np.exp(-ndw ** 2 / (2 * ds)) / np.sqrt(2 * np.pi * ds ** 3)
    else:
        return dw * np.exp(-dw ** 2 / (2 * ds)) / np.sqrt(2 * np.pi * ds ** 3)


def mu(St, a):
    return (1 + (2 ** a - 1) * St) ** (1 / a)


def f_ec(S1, S0, w1, w0):
    dw = w1 - w0
    dS = S1 - S0
    nu0 = w0 ** 2 / S0
    A0 = 0.8661 * (1 - 0.133 * nu0 ** (-0.615))
    A1 = 0.308 * nu0 ** (-0.115)
    A2 = 0.0373 * nu0 ** (-0.115)
    Sbar = dS / S0
    A3 = A0 ** 2 + 2 * A0 * A1 * np.sqrt(dS * Sbar) / dw
    return A0 * (2 * np.pi) ** (-0.5) * dw * dS ** (-1.5) * \
           np.exp(-0.5 * A1 ** 2 * Sbar) * (
                   np.exp(-0.5 * A3 * dw ** 2 / dS) + A2 * Sbar ** 1.5 * (1 + 2 * A1 * np.sqrt(Sbar / np.pi)))
    # return 2*A0*(2*np.pi)**(-0.5)*\
    #       np.exp(-0.5*A1**2*Sbar)*(np.exp(-0.5*A3*dw**2/dS)+A2*Sbar**1.5*(1+2*A1*np.sqrt(Sbar/np.pi)))


def f_sc(S1, S0, w1, w0):
    dw = w1 - w0
    ds = S1 - S0
    return (2 * np.pi) ** -0.5 * dw * ds ** (-1.5) * np.exp(-0.5 * dw ** 2 / ds)


def proba(M, zf, frac=0.5, acc=1000, zi=0.0, sig8=sigma8, h=h, kmax=30, window='TopHat', prec=1000, om0=om,
          ol0=oml, omb=omb, camb=False, model='press', colos=False, A=0.322, a=0.707, p=0.3):
    """

    :param M: float. mass of the halo considered
    :param zf: float or ndarray. formation redshift(s) at which we want to calculate the probability
    :param frac: float between 0 and 1. Fraction of mass to define formation redshift. Default :0.5
    :param acc: int. Number redshift steps. Default : 1000.
    :param zi: float. Observed redshift of considered halo. Default :0.
    :param sig8: float : sigma 8 cosmo parameter
    :param h: float : H0/100 cosmo parameter
    :param kmax: float or int : maximum wavenumber for CAMB power spectrum.
    :param window:  str : type of smoothing window function. either "TopHat", "Gauss" or k-Sharp'.
    :param prec: int : number of bins for integral calculations.
    :param om0: float : fraction matter density
    :param ol0: float : fraction dark energy density
    :param omb: float : fraction baryon density
    :param camb:  boolean : if using camb spectrum or analytical version of Eisenstein and Hu.
    :param model: if Press&Schechter mass function "press" or sheth &tormen "sheth"
    :param colos: :param Colos : boolan : using Colossus halo mass function or not
    :param A: float. normalisation in Sheth & Tormen fonctional
    :param a: float. multiplication scaling of peak height in sheth & tormen fonctional
    :param p: float. Power of peak heigh in Sheth & Tormen halo mass function
    :return: Probability density function of redshift at which halos had x fraction of their mass
    """
    S0 = sigma(M, sig8, h, kmax, window, 'M', prec, om0, ol0, omb, camb, colos) ** 2  # variance of the field at mass M
    Sh = sigma(M * frac, sig8, h, kmax, window, 'M', prec, om0, ol0, omb, camb, colos) ** 2  # variance at mass frac*M
    w0 = delta_c(zi, om0, ol0)  # critical density at observed redshift
    if type(zf) == np.ndarray:  # for probability distribution
        mass = np.logspace(np.log10(M * frac), np.log10(M), acc)  # masses to calculate the integral
        l = len(zf)  # number of steps in PDF
        mat_zf = np.array([zf] * acc)  # (acc, l)
        S = sigma(mass, sig8, h, kmax, window, 'M', prec, om0, ol0, omb, camb,
                  colos) ** 2  # variance of all masses (acc,)
        # masses for integral
        mat_mass = np.array([mass] * l).transpose()  # duplicating mass array to vectorize calculations  (acc, l)
        mat_S = np.array([S] * l).transpose()  # duplicating var array to vectorize calculations  (acc, l)
        mat_wf = delta_c(mat_zf, om0, ol0)  # critical density for all z_f
        mat_wt = (mat_wf - w0) / np.sqrt(Sh - S0)  # normalisation following lacey&Cole eq 2.27
        # mat_S = sigma(mat_mass, sig8, h, kmax, window, 'M', prec, om0, ol0, omb, camb, colos)**2
        mat_St = (mat_S - S0) / (Sh - S0)  # normalisation following lacey&Cole eq 2.27 (acc, l)
        mat_St[-1, :] = 1e-10  # to avoid integration problems and deviding by 0
        mat_Ks = K(mat_St, mat_wt, model, A, a, p)  # function as defined in lacey & cole eq (2.29)
        mat_ds = (mat_St[2:, :] - mat_St[:-2, :]) * 0.5  # differential of variance S(M)
        return -M * np.sum(mat_ds * mat_Ks[1:-1, :] / mat_mass[1:-1, :], axis=0)
    else:
        mass = np.logspace(np.log10(M * frac), np.log10(M), acc)  # masses to calculate the integral
        wf = delta_c(zf, om0, ol0)  # critical density for all z_f
        wt = (wf - w0) / np.sqrt(Sh - S0)  # normalisation following lacey&Cole eq 2.27
        S = sigma(mass, sig8, h, kmax, window, 'M', prec, om0, ol0, omb, camb,
                  colos) ** 2  # variance of all masses (acc,)
        St = (S - S0) / (Sh - S0)  # normalisation following lacey&Cole eq 2.27
        # St[-1] = 1e-10
        Ks = K(St, wt, model, A, a, p)  # function as defined in lacey & cole eq (2.29)
        ds = (St[2:] - St[:-2]) * 0.5  # differential of variance S(M)
        return -M * np.sum(ds * Ks[1:-1] / mass[1:-1])


def new_proba(M, zf, frac=0.5, acc=10000, zi=0.0, sig8=sigma8, h=h, kmax=30, window='TopHat', prec=1000, om0=om,
              ol0=oml, omb=omb, camb=False, model='sheth', colos=False):
    S0 = sigma(M, sig8, h, kmax, window, 'M', prec, om0, ol0, omb, camb, colos) ** 2
    Sh = sigma(M * frac, sig8, h, kmax, window, 'M', prec, om0, ol0, omb, camb, colos) ** 2
    w0 = delta_c(zi, om0, ol0)
    if type(zf) == np.ndarray:
        mass = np.logspace(np.log10(M * frac), np.log10(M), acc)  # size (0, acc)
        l = len(zf)
        sigs = sigma(mass, sig8, h, kmax, window, 'M', prec, om0, ol0, omb, camb, colos) ** 2 - S0  # (acc,)
        mat_zf = np.array([zf] * acc)  # (acc, l)
        mat_mass = np.array([mass] * l).transpose()  # (acc, l)
        mat_wf = delta_c(mat_zf, om0, ol0) - w0  # (acc, l)
        # mat_wt = (mat_wf-w0)/np.sqrt(Sh-S0)
        mat_S = np.array([sigs] * l).transpose()  # (acc, l)
        mat_S[-1, :] = 1e-10
        mat_nu = mat_wf / np.sqrt(mat_S)  # (acc, l)
        # mat_St = (mat_S - S0)/(Sh - S0)   # (acc, l)
        # mat_St[-1, :] = 1e-10
        if model == 'EC':
            mat_f = f_ec(mat_S[:, :] + S0, S0, mat_wf[:, :] + w0, w0)
            mat_ds = 0.5 * (mat_S[2:, :] - mat_S[:-2, :])
            # mat_dnu = (mat_nu[2:, :] - mat_nu[:-2,:])*0.5  #(acc-3, l)
            # mat_dm = 0.5*(mat_mass[2:, :] - mat_mass[:-2, :])
            return -M * np.sum(mat_ds * mat_f[1:-1, :] / mat_mass[1:-1, :], axis=0)
        else:
            mat_f = fps(mat_nu[:-1, :]) / mat_nu[:-1, :]  # (acc-1, l)
            # mat_f = fps(mat_nu[:-1, :])
            mat_dnu = (mat_nu[2:-1, :] - mat_nu[:-3, :]) * 0.5  # (acc-3, l)
            # mat_Ks = K(mat_S, mat_wf, model, A, a, p)
            # mat_ds = (mat_S[2:, :] - mat_S[:-2,:])*0.5
            return M * np.sum(mat_dnu * mat_f[1:-1, :] / mat_mass[1:-2, :], axis=0)  # (acc-3, l)
    else:
        mass = np.logspace(np.log10(M * frac), np.log10(M), acc)
        wf = delta_c(zf, om0, ol0) - w0
        # St = np.logspace(-10, 0, acc)
        S = sigma(mass, sig8, h, kmax, window, 'M', prec, om0, ol0, omb, camb, colos) ** 2 - S0
        S[-1] = 1e-10
        nu = wf / np.sqrt(S)
        if model == 'EC':
            f = f_ec(S + S0, S0, wf + w0, w0)
            ds = 0.5 * (S[2:] - S[:-2])
            return -M * np.sum(ds * f[1:-1] / mass[1:-1])
        else:
            f = fps(nu) / nu
            dnu = (nu[2:] - nu[:-2]) * 0.5
            return M * np.sum(dnu * f[1:-1] / mass[1:-1])


def M_integ_proba(masses, weights=None, zf=np.linspace(0, 7, 20), frac=0.5, acc=10000, zi=0.0, sig8=sigma8, h=h,
                  kmax=30, window='TopHat', prec=1000, om0=om, diff = False,
                  ol0=oml, omb=omb, camb=False, model='sheth', colos=False):
    res = []
    if not (type(weights) == np.ndarray or type(weights) == list):
        for mass in masses:
            if diff:
                prob = new_proba(mass, zf, frac, acc, zi, sig8, h, kmax, window, prec, om0, ol0, omb, camb,
                                 model, colos)
                dz = zf[2:] - zf[:-2]
                res.append((prob[2:]-prob[:-2])/dz)
            else:
                res.append(new_proba(mass, zf, frac, acc, zi, sig8, h, kmax, window, prec, om0, ol0, omb, camb,
                                     model, colos))
        ares = np.array(res)
        return np.sum(ares, axis=0) / len(masses)
    else:
        for i in range(len(masses)):
            mass = masses[i]
            w = weights[i] / np.sum(weights)
            if diff:
                prob = new_proba(mass, zf, frac, acc, zi, sig8, h, kmax, window, prec, om0, ol0, omb, camb,
                                 model, colos)
                dz = zf[2:] - zf[:-2]
                res.append(-(prob[2:]-prob[:-2])*w/dz)
            else:
                res.append(new_proba(mass, zf, frac, acc, zi, sig8, h, kmax, window, prec, om0, ol0, omb, camb,
                                     model, colos) * w)
        ares = np.array(res)
        return np.sum(ares, axis=0)


folder1 = '/home/yuba/mint2020/Illustris-3/output/groups_099/'
folder2 = '/home/yuba/reading_gadget/'

'''# #masses = np.logspace(8, 14, 50)
# #histmass = np.loadtxt(folder1+'histmas3e14plus.txt')
# histmass2 = np.loadtxt(folder2+'m30s08_histmas1_3e14.txt')
# histmass3 = np.loadtxt(folder2+'m30s08_histmas1_3e13.txt')
# histmass4 = np.loadtxt(folder2+'m30s08_histmas1_3e12.txt')
# #histmass5 = np.loadtxt(folder1+'histmas1to3e11.txt')
# #cumsum = np.loadtxt(folder1+'cum_histo_3e14plus.txt')
# cumsum2 = np.loadtxt(folder2+'m30s08_cum_histo_1to3e14.txt')
# cumsum3 = np.loadtxt(folder2+'m30s08_cum_histo_1to3e13.txt')
# cumsum4 = np.loadtxt(folder2+'m30s08_cum_histo_1to3e12.txt')
# #cumsum5 = np.loadtxt(folder1+'cum_histo_1to3e11.txt')
# #poisson = np.loadtxt(folder1+'poisson_errors_3e14plus.txt')
# poisson2 = np.loadtxt(folder2+'m30s08_poisson_errors_1to3e14.txt')
# poisson3 = np.loadtxt(folder2+'m30s08_poisson_errors_1to3e13.txt')
# poisson4 = np.loadtxt(folder2+'m30s08_poisson_errors_1to3e12.txt')
# #poisson5 = np.loadtxt(folder1+'poisson_errors_1to3e11.txt')

#masses = np.logspace(8, 14, 50)
#histmass = np.loadtxt(folder1+'histmas3e14plus.txt')

#simulations = ['m_m11', 'm_m11m', 'm_m22', 'm_m22m', 'm_m44', 'm_m44m']
#simulations = ['m_limit', 'b_limit', 'i_limit']
#simulations = ['m_illustris_1000', 'm_m30s08_1000','m_bolshoi_1000']
simulations = ['diff_m25s7', 'diff_m25s8', 'diff_m25s9']
sig8s = [0.7,0.8,0.9]
types = ['low']
diff = True
for i in range(len(simulations)):
    s8 = sig8s[i]
    om0 = 0.25
    Mmins = [1e12, 1e13, 1e14]
    Mmaxs = [2e12, 2e13, 2e14]
    # histmass2 = np.loadtxt(folder2+'mdr1_histmas1_3e14.txt')
    # histmass3 = np.loadtxt(folder2+'mdr1_histmas1_3e13.txt')
    # histmass4 = np.loadtxt(folder2+'mdr1_histmas1_3e12.txt')
    histmass2 = np.loadtxt(folder1+'{}_{:2.1e}_{:2.1e}_histmass.txt'.format(simulations[i], Mmins[0], Mmaxs[0]))
    histmass3 = np.loadtxt(folder1+'{}_{:2.1e}_{:2.1e}_histmass.txt'.format(simulations[i], Mmins[1], Mmaxs[1]))
    histmass4 = np.loadtxt(folder1+'{}_{:2.1e}_{:2.1e}_histmass.txt'.format(simulations[i], Mmins[2], Mmaxs[2]))

    #histmass5 = np.loadtxt(folder2+'mdr1_histmas1_3e11.txt')
    #cumsum = np.loadtxt(folder1+'cum_histo_3e14plus.txt')
    # cumsum2 = np.loadtxt(folder2+'mdr1_cum_histo_1to3e14.txt')
    # cumsum3 = np.loadtxt(folder2+'mdr1_cum_histo_1to3e13.txt')
    # cumsum4 = np.loadtxt(folder2+'mdr1_cum_histo_1to3e12.txt')

    # res = M_integ_proba(masses1, weights1, acc= 100000, model='EC', zf=zf, colos=True, om0=0.3089, omb=0.0486, sig8=0.8159,  h=0.6774)
    # masses1 = histmass[1]*1e10
    # weights1 = histmass[0]
    masses2 = histmass2[1]
    weights2 = histmass2[0]
    masses3 = histmass3[1]
    weights3 = histmass3[0]
    masses4 = histmass4[1]
    weights4 = histmass4[0]
    # masses5 = histmass5[1]*1
    # weights5 = histmass5[0]
    zf = np.linspace(0.05, 2.5, 100)

    dz = zf[1] - zf[0]
    res2 = M_integ_proba(masses2, weights2, acc=100000, model='EC', zf=zf, colos=True, ol0=1 - om0, om0=om0, omb=0.0486,
                         sig8=s8, h=0.7, diff=diff)
    res3 = M_integ_proba(masses3, weights3, acc=100000, model='EC', zf=zf, colos=True, ol0=1 - om0, om0=om0, omb=0.0486,
                         sig8=s8, h=0.7, diff=diff)
    res4 = M_integ_proba(masses4, weights4, acc=100000, model='EC', zf=zf, colos=True, ol0=1 - om0, om0=om0, omb=0.0486,
                         sig8=s8, h=0.7, diff=diff)

    # res5 = M_integ_proba(masses5, weights5, acc= 100000, model='EC', zf=zf, colos=True, om0=om0, ol0=1-om0, omb=0.0486, sig8=0.82,  h=0.7)
    for typ in types:
        cumsum2 = np.loadtxt(folder1+'{}_cum_histo_{:2.1e}_{:2.1e}.txt'.format(simulations[i],  Mmins[0], Mmaxs[0]))
        cumsum3 = np.loadtxt(folder1+'{}_cum_histo_{:2.1e}_{:2.1e}.txt'.format(simulations[i],  Mmins[1], Mmaxs[1]))
        cumsum4 = np.loadtxt(folder1+'{}_cum_histo_{:2.1e}_{:2.1e}.txt'.format(simulations[i],  Mmins[2], Mmaxs[2]))

        cumsum2m = np.loadtxt(folder1+'{}_cum_histo_{:2.1e}_{:2.1e}.txt'.format(simulations[i],  Mmins[0], Mmaxs[0]))
        cumsum3m = np.loadtxt(folder1+'{}_cum_histo_{:2.1e}_{:2.1e}.txt'.format(simulations[i],  Mmins[1], Mmaxs[1]))
        cumsum4m = np.loadtxt(folder1+'{}_cum_histo_{:2.1e}_{:2.1e}.txt'.format(simulations[i],  Mmins[2], Mmaxs[2]))
        #cumsum5 = np.loadtxt(folder2+'mdr1_cum_histo_1to3e11.txt')
        #poisson = np.loadtxt(folder+'poisson_errors_3e14plus.txt')
        # poisson2 = np.loadtxt(folder2+'mdr1_poisson_errors_1to3e14.txt')
        # poisson3 = np.loadtxt(folder2+'mdr1_poisson_errors_1to3e13.txt')
        # poisson4 = np.loadtxt(folder2+'mdr1_poisson_errors_1to3e12.txt')

        poisson2 = np.loadtxt(folder1+'{}_poisson_errors_{:2.1e}_{:2.1e}.txt'.format(simulations[i],  Mmins[0], Mmaxs[0]))
        poisson3 = np.loadtxt(folder1+'{}_poisson_errors_{:2.1e}_{:2.1e}.txt'.format(simulations[i],  Mmins[1], Mmaxs[1]))
        poisson4 = np.loadtxt(folder1+'{}_poisson_errors_{:2.1e}_{:2.1e}.txt'.format(simulations[i],  Mmins[2], Mmaxs[2]))
        #poisson5 = np.loadtxt(folder2+'mdr1_poisson_errors_1to3e11.txt')
        poisson2m = np.loadtxt(folder1+'{}_poisson_errors_{:2.1e}_{:2.1e}.txt'.format(simulations[i],  Mmins[0], Mmaxs[0]))
        poisson3m = np.loadtxt(folder1+'{}_poisson_errors_{:2.1e}_{:2.1e}.txt'.format(simulations[i], Mmins[1], Mmaxs[1]))
        poisson4m = np.loadtxt(folder1+'{}_poisson_errors_{:2.1e}_{:2.1e}.txt'.format(simulations[i],  Mmins[2], Mmaxs[2]))


        #dpdz = -(np.array(res)[2:] - np.array(res)[:-2])*0.5/dz
        #plt.plot(zf, res, label='Lacey and Cole '+ '$M > 3e14$', color='red', linewidth=2)
        #plt.plot(zf, res, label='EC '+ '$M > 3e14$', color='red', linewidth=2)
        #plt.errorbar(cumsum[0], cumsum[1],linestyle='--', yerr=poisson,  label= 'Illustris halos'+ '$M>3e14$', color='red',linewidth=2)
        #plt.plot(zf, res2, label='Lacey and Cole '+ '$ 1e14<M<3e14$', color='blue', linewidth=2)
        plt.plot(zf[1:-1], res2, label='EC {:2.1e}<M<{:2.1e}'.format(Mmins[0], Mmaxs[0]), color='blue', linewidth=2)
        # plt.errorbar(cumsum2[0], cumsum2[1], linestyle='--', yerr=poisson2,
        #              label='{} {:2.1e}<M<{:2.1e}'.format(simulations[i], Mmins[0], Mmaxs[0]), color='blue', linewidth=2)
        plt.plot(cumsum2[0], cumsum2[1], drawstyle='steps-mid', linestyle='--',
                     label='{} {:2.1e}<M<{:2.1e}'.format(simulations[i], Mmins[0], Mmaxs[0]), color='blue', linewidth=2)

        #plt.errorbar(cumsum2m[0], cumsum2m[1], linestyle='-.', yerr=poisson2m,
                     #label='{}m {:2.1e}<M<{:2.1e}'.format(simulation, Mmins[0], Mmaxs[0]), color='blue', linewidth=2)
        #plt.plot(zf, res3, label='Lacey and Cole '+ '$ 1e13<M<5e13$', color='black', linewidth=2)
        plt.plot(zf[1:-1], res3, label='EC {:2.1e}<M<{:2.1e}'.format(Mmins[1], Mmaxs[1]), color='black', linewidth=2)
        # plt.errorbar(cumsum3[0], cumsum3[1], linestyle='--', yerr=poisson3,
        #              label='{} {:2.1e}<M<{:2.1e}'.format(simulations[i], Mmins[1], Mmaxs[1]), color='black', linewidth=2)
        plt.plot(cumsum3[0], cumsum3[1], drawstyle='steps-mid', linestyle='--',
                     label='{} {:2.1e}<M<{:2.1e}'.format(simulations[i], Mmins[1], Mmaxs[1]), color='black', linewidth=2)

        #plt.errorbar(cumsum3m[0], cumsum3m[1], linestyle='-.', yerr=poisson2m,
                     #label='{}m {:2.1e}<M<{:2.1e}'.format(simulation, Mmins[0], Mmaxs[0]), color='black', linewidth=2)
        #plt.plot(zf, res4, label='Lacey and Cole '+ '$ 1e12<M<3e12$', color='green', linewidth=2)
        plt.plot(zf[1:-1], res4, label='EC {:2.1e}<M<{:2.1e}'.format(Mmins[2], Mmaxs[2]), color='green', linewidth=2)
        #plt.errorbar(cumsum4[0], cumsum4[1], linestyle='--', yerr=poisson4,
                     #label='{} {:2.1e}<M<{:2.1e}'.format(simulations[i], Mmins[2], Mmaxs[2]), color='green', linewidth=2)
        plt.plot(cumsum4[0], cumsum4[1], drawstyle='steps-mid', linestyle='--',
                     label='{} {:2.1e}<M<{:2.1e}'.format(simulations[i], Mmins[2], Mmaxs[2]), color='green', linewidth=2)

        # plt.errorbar(cumsum4m[0], cumsum4m[1], linestyle='-.', yerr=poisson2m,
        #              label='{}m {:2.1e}<M<{:2.1e}'.format(simulation, Mmins[0], Mmaxs[0]), color='green', linewidth=2)
        #plt.plot(zf, res5, label='Lacey and Cole '+ '$ 1e11<M<3e11$', color='grey', linewidth=2)
        #plt.plot(zf, res5, label='EC '+ '$ 1e11<M<3e11$', color='grey', linewidth=2)
        #plt.errorbar(cumsum5[0], cumsum5[1], linestyle='--', yerr=poisson5, label= 'Illustris halos'+ '$ 1e11<M<3e11$', color='grey', linewidth=2)
        plt.xlabel('z - $z_{max}$', size=20)
        plt.xlim(0, 2.5)
        plt.ylabel('P($Z_{50} > z$)', size=20)
        plt.legend()
        #plt.savefig('z50_distrib_compar.png',bbox_inches ='tight', dpi=1100)
        #plt.plot(zf[1:-1], dpdz)

        #plt.savefig('z50_{}.png'.format(simulations[i]), dpi=700, bbox_inches='tight')
        plt.show()'''

save = False
diff = True
corr = True
#simulations = ['ndiff_illustris', 'ndiff_m3s8', 'ndiff_bolshoi']
#simulations = ['nillustris', 'nm3s8', 'nbolshoi']
if diff:
    #simulations = ['diff_m25s7', 'diff_m25s8', 'diff_m25s9']
    simulations = ['diff_illustris', 'diff_m3s8','diff_bolshoiP', 'diff_bolshoi']
else:
    #simulations = ['m25s7', 'm25s8', 'm25s9']
    simulations = ['illustris', 'm3s8', 'bolshoiP', 'bolshoi']
Mmins = [1e12, 1e13, 1e14]
# Mmins = [1e12, 1e13, 1e14]
Mmaxs = [3e12, 3e13, 3e14]
lens = len(simulations)
lenm = len(Mmins)
#sig8s = [0.7,0.8,0.9]
#sig8s = [0.7, 0.8, 0.9]
omgs = [0.31, 0.3, 0.31, 0.27]
sig8s = [0.81, 0.8, 0.82, 0.82]
types = ['low']

zx = 0.5
res2 = []
res3 = []
res4 = []
cumsum2 = []
cumsum3 = []
cumsum4 = []
poisson2 = []
poisson3 = []
poisson4 = []
for i in range(len(simulations)):
    s8 = sig8s[i]
    #s8 = 0.8
    om0 = omgs[i]
    histmass2 = np.loadtxt(folder1+'{}_{:2.1e}_{:2.1e}_histmass.txt'.format(simulations[i], Mmins[0], Mmaxs[0]))
    histmass3 = np.loadtxt(folder1+'{}_{:2.1e}_{:2.1e}_histmass.txt'.format(simulations[i], Mmins[1], Mmaxs[1]))
    histmass4 = np.loadtxt(folder1+'{}_{:2.1e}_{:2.1e}_histmass.txt'.format(simulations[i], Mmins[2], Mmaxs[2]))

    # histmass2 = np.loadtxt(folder1+'{}_{:2.1e}_{:2.1e}_histmass.txt'.format(simulations[i], Mmins[0], Mmaxs[0]))
    # histmass3 = np.loadtxt(folder1+'{}_{:2.1e}_{:2.1e}_histmass.txt'.format(simulations[i], Mmins[1], Mmaxs[1]))
    # histmass4 = np.loadtxt(folder1+'{}_{:2.1e}_{:2.1e}_histmass.txt'.format(simulations[i], Mmins[2], Mmaxs[2]))
    masses2 = histmass2[1]
    weights2 = histmass2[0]
    masses3 = histmass3[1]
    weights3 = histmass3[0]
    masses4 = histmass4[1]
    weights4 = histmass4[0]
    if corr:
        zf = np.linspace(0.05, 3, 100)
    else:
        zf = np.linspace(0.01, 3, 100)
    dz = zf[1] - zf[0]
    if save:
        res2.append(M_integ_proba(masses2, weights2, frac=zx, acc=100000, model='EC', zf=zf, zi=zf[0]-0.01, colos=True, ol0=1 - om0, om0=om0, omb=0.0486,
                             sig8=s8, h=0.7, diff=diff))
        res3.append(M_integ_proba(masses3, weights3, frac=zx, acc=100000, model='EC', zf=zf, zi=zf[0]-0.01, colos=True, ol0=1 - om0, om0=om0, omb=0.0486,
                             sig8=s8, h=0.7, diff=diff))
        res4.append(M_integ_proba(masses4, weights4, frac=zx, acc=100000, model='EC', zf=zf, zi=zf[0]-0.01, colos=True, ol0=1 - om0, om0=om0, omb=0.0486,
                             sig8=s8, h=0.7, diff=diff))
    else:
        if diff:
            if corr:
                res2 = np.loadtxt('res2_dpdz_corr_{}_{}.txt'.format(Mmins[0], Mmaxs[0]))
                res3 = np.loadtxt('res3_dpdz_corr_{}_{}.txt'.format(Mmins[1], Mmaxs[1]))
                res4 = np.loadtxt('res4_dpdz_corr_{}_{}.txt'.format(Mmins[2], Mmaxs[2]))
            else:
                res2 = np.loadtxt('res2_dpdz_{}_{}.txt'.format(Mmins[0], Mmaxs[0]))
                res3 = np.loadtxt('res3_dpdz_{}_{}.txt'.format(Mmins[1], Mmaxs[1]))
                res4 = np.loadtxt('res4_dpdz_{}_{}.txt'.format(Mmins[2], Mmaxs[2]))
        else:
            if corr:
                res2 = np.loadtxt('res2_z50_corr_{}_{}.txt'.format(Mmins[0], Mmaxs[0]))
                res3 = np.loadtxt('res3_z50_corr_{}_{}.txt'.format(Mmins[1], Mmaxs[1]))
                res4 = np.loadtxt('res4_z50_corr_{}_{}.txt'.format(Mmins[2], Mmaxs[2]))
            else:
                res2 = np.loadtxt('res2_z50_{}_{}.txt'.format(Mmins[0], Mmaxs[0]))
                res3 = np.loadtxt('res3_z50_{}_{}.txt'.format(Mmins[1], Mmaxs[1]))
                res4 = np.loadtxt('res4_z50_{}_{}.txt'.format(Mmins[2], Mmaxs[2]))

    for typ in types:
        # cumsum2.append(np.loadtxt(folder1+'{}_{}_cum_histo_{:2.1e}_{:2.1e}.txt'.format(simulations[i], 100*zx,  Mmins[0], Mmaxs[0])))
        # cumsum3.append(np.loadtxt(folder1+'{}_{}_cum_histo_{:2.1e}_{:2.1e}.txt'.format(simulations[i], 100*zx, Mmins[1], Mmaxs[1])))
        # cumsum4.append(np.loadtxt(folder1+'{}_{}_cum_histo_{:2.1e}_{:2.1e}.txt'.format(simulations[i], 100*zx, Mmins[2], Mmaxs[2])))
        #
        #
        if corr:
            cumsum2.append(np.loadtxt(folder1+'c{}_cum_histo_{:2.1e}_{:2.1e}.txt'.format(simulations[i], Mmins[0], Mmaxs[0])))
            cumsum3.append(np.loadtxt(folder1+'c{}_cum_histo_{:2.1e}_{:2.1e}.txt'.format(simulations[i], Mmins[1], Mmaxs[1])))
            cumsum4.append(np.loadtxt(folder1+'c{}_cum_histo_{:2.1e}_{:2.1e}.txt'.format(simulations[i], Mmins[2], Mmaxs[2])))
            poisson2.append(np.loadtxt(folder1 + 'c{}_poisson_errors_{:2.1e}_{:2.1e}.txt'.format(simulations[i], Mmins[0], Mmaxs[0])))
            poisson3.append(np.loadtxt(folder1 + 'c{}_poisson_errors_{:2.1e}_{:2.1e}.txt'.format(simulations[i], Mmins[1], Mmaxs[1])))
            poisson4.append(np.loadtxt(folder1 + 'c{}_poisson_errors_{:2.1e}_{:2.1e}.txt'.format(simulations[i], Mmins[2], Mmaxs[2])))

        else:
            cumsum2.append(np.loadtxt(folder1+'{}_cum_histo_{:2.1e}_{:2.1e}.txt'.format(simulations[i], Mmins[0], Mmaxs[0])))
            cumsum3.append(np.loadtxt(folder1+'{}_cum_histo_{:2.1e}_{:2.1e}.txt'.format(simulations[i], Mmins[1], Mmaxs[1])))
            cumsum4.append(np.loadtxt(folder1+'{}_cum_histo_{:2.1e}_{:2.1e}.txt'.format(simulations[i], Mmins[2], Mmaxs[2])))
            poisson2.append(np.loadtxt(folder1+'{}_poisson_errors_{:2.1e}_{:2.1e}.txt'.format(simulations[i], Mmins[0], Mmaxs[0])))
            poisson3.append(np.loadtxt(folder1+'{}_poisson_errors_{:2.1e}_{:2.1e}.txt'.format(simulations[i], Mmins[1], Mmaxs[1])))
            poisson4.append(np.loadtxt(folder1+'{}_poisson_errors_{:2.1e}_{:2.1e}.txt'.format(simulations[i], Mmins[2], Mmaxs[2])))
# #
if save:
    if diff:
        if corr:
            np.savetxt('res2_dpdz_corr_{}_{}.txt'.format(Mmins[0], Mmaxs[0]), np.array(res2))
            np.savetxt('res3_dpdz_corr_{}_{}.txt'.format(Mmins[1], Mmaxs[1]), np.array(res3))
            np.savetxt('res4_dpdz_corr_{}_{}.txt'.format(Mmins[2], Mmaxs[2]), np.array(res4))
        else:
            np.savetxt('res2_dpdz_{}_{}.txt'.format(Mmins[0], Mmaxs[0]), np.array(res2))
            np.savetxt('res3_dpdz_{}_{}.txt'.format(Mmins[1], Mmaxs[1]), np.array(res3))
            np.savetxt('res4_dpdz_{}_{}.txt'.format(Mmins[2], Mmaxs[2]), np.array(res4))
    else:
        if corr:
            np.savetxt('res2_z50_corr_{}_{}.txt'.format(Mmins[0], Mmaxs[0]), np.array(res2))
            np.savetxt('res3_z50_corr_{}_{}.txt'.format(Mmins[1], Mmaxs[1]), np.array(res3))
            np.savetxt('res4_z50_corr_{}_{}.txt'.format(Mmins[2], Mmaxs[2]), np.array(res4))
        else:
            np.savetxt('res2_z50_{}_{}.txt'.format(Mmins[0], Mmaxs[0]), np.array(res2))
            np.savetxt('res3_z50_{}_{}.txt'.format(Mmins[1], Mmaxs[1]), np.array(res3))
            np.savetxt('res4_z50_{}_{}.txt'.format(Mmins[2], Mmaxs[2]), np.array(res4))

colors = ['blue', 'black', 'green']
plt.figure()
for i in range(lenm):
    if diff:
        plt.plot(zf[1:-1], res2[i], label='EC', color=colors[i], linewidth=2)
        plt.plot(cumsum2[i][0], cumsum2[i][1], linestyle='--', drawstyle='steps-mid', label=' {}'.format(simulations[i][5:]),
                 color=colors[i], linewidth=2)
        plt.fill_between(cumsum2[i][0], cumsum2[i][1] - poisson2[i],cumsum2[i][1] + poisson2[i],  color=colors[i],alpha=0.2)

        # plt.errorbar(cumsum2[i][0], cumsum2[i][1], linestyle='--', yerr=poisson2[i], label=' {}'.format(simulations[i][5:]),
        #      color=colors[i], drawstyle='steps-mid', linewidth=2)
    else:
        plt.plot(zf, res2[i], label='EC', color=colors[i], linewidth=2)
        #plt.errorbar(cumsum2[i][0], cumsum2[i][1], linestyle='--', yerr=poisson2[i], label=' {}'.format(simulations[i]),
                     #color=colors[i], linewidth=2)
        plt.plot(cumsum2[i][0], cumsum2[i][1], linestyle='--', alpha=0.7, label=' {}'.format(simulations[i]),
                 color=colors[i], linewidth=2)
        plt.fill_between(cumsum2[i][0], cumsum2[i][1] - poisson2[i],cumsum2[i][1] + poisson2[i],  color=colors[i],alpha=0.2)
plt.xlabel('z', size=20)
plt.xlim(0.01, 2.5)
#plt.ylim(0, 3)
if diff:
    plt.ylabel('dP/dz', size=20)
else:
    plt.ylabel('P($Z_{50} > z$)', size=20)
#plt.legend()
if corr:
    plt.title('with infall {:2.1e}<M<{:2.1e}'.format(Mmins[0], Mmaxs[0]))
    if diff:
        plt.savefig('dpdz_corr_{:2.1e}<M<{:2.1e}_bim.png'.format(Mmins[0], Mmaxs[0]), dpi=100, bbox_inches='tight')
    else:
        plt.savefig('z50_corr_{:2.1e}<M<{:2.1e}_bim.png'.format(Mmins[0], Mmaxs[0]), dpi=100, bbox_inches='tight')
else:
    plt.title('{:2.1e}<M<{:2.1e}'.format(Mmins[0], Mmaxs[0]))
    if diff:
        plt.savefig('dpdz_{:2.1e}<M<{:2.1e}_bim.png'.format(Mmins[0], Mmaxs[0]), dpi=100, bbox_inches='tight')
    else:
        plt.savefig('z50_{:2.1e}<M<{:2.1e}_bim.png'.format(Mmins[0], Mmaxs[0]), dpi=100, bbox_inches='tight')
plt.show()



plt.figure()
for i in range(lenm):
    if diff:
        plt.plot(zf[1:-1], res3[i], label='EC', color=colors[i], linewidth=2)
        plt.plot(cumsum3[i][0], cumsum3[i][1], linestyle='--', drawstyle='steps-mid',
                 label=' {}'.format(simulations[i][5:]), color=colors[i], linewidth=2)
        plt.fill_between(cumsum3[i][0], cumsum3[i][1] - poisson3[i],cumsum3[i][1] + poisson3[i], color=colors[i], alpha=0.2)
        # plt.errorbar(cumsum3[i][0], cumsum3[i][1], linestyle='--', drawstyle='steps-mid',yerr=poisson3[i],
        #              label=' {} '.format(simulations[i][5:]), color=colors[i], linewidth=2)
    else:
        plt.plot(zf, res3[i], label='EC', color=colors[i], linewidth=2)
        # plt.errorbar(cumsum3[i][0], cumsum3[i][1], linestyle='--', yerr=poisson3[i],
        #              label=' {} '.format(simulations[i]), color=colors[i], linewidth=2)
        plt.plot(cumsum3[i][0], cumsum3[i][1], linestyle='--', alpha=0.7, label=' {}'.format(simulations[i][:]),
                 color=colors[i], linewidth=2)

        plt.fill_between(cumsum3[i][0], cumsum3[i][1] - poisson3[i],cumsum3[i][1] + poisson3[i], color=colors[i], alpha=0.2)
plt.xlabel('z ', size=20)
plt.xlim(0.01, 2)
#plt.ylim(0, 4)
# if diff:
#     plt.ylabel('dP/dz', size=20)
# else:
#     plt.ylabel('P($Z_{50} > z$)', size=20)
# plt.legend()
if corr:
    plt.title('with infall {:2.1e}<M<{:2.1e}'.format(Mmins[1], Mmaxs[1]))
    if diff:
        plt.savefig('dpdz_corr_{:2.1e}<M<{:2.1e}_bim.png'.format(Mmins[1], Mmaxs[1]), dpi=100, bbox_inches='tight')
    else:
        plt.savefig('z50_corr_{:2.1e}<M<{:2.1e}_bim.png'.format(Mmins[1], Mmaxs[1]), dpi=100, bbox_inches='tight')
else:
    plt.title('{:2.1e}<M<{:2.1e}'.format(Mmins[1], Mmaxs[1]))
    if diff:
        plt.savefig('dpdz_{:2.1e}<M<{:2.1e}_bim.png'.format(Mmins[1], Mmaxs[1]), dpi=100, bbox_inches='tight')
    else:
        plt.savefig('z50_{:2.1e}<M<{:2.1e}_bim.png'.format(Mmins[1], Mmaxs[1]), dpi=100, bbox_inches='tight')
plt.show()

plt.figure()
for i in range(lenm):
    if diff:
        plt.plot(zf[1:-1], res4[i], label='EC', color=colors[i], linewidth=2)
        plt.plot(cumsum4[i][0], cumsum4[i][1], linestyle='--', drawstyle='steps-mid',
                 label=' {}'.format(simulations[i][5:]), color=colors[i], linewidth=2)
        plt.fill_between(cumsum4[i][0], cumsum4[i][1] - poisson4[i],cumsum4[i][1] + poisson4[i],  color=colors[i],alpha=0.2)

        # plt.errorbar(cumsum4[i][0], cumsum4[i][1], linestyle='--', yerr=poisson4[i],drawstyle='steps-mid',
        #              label=' {} '.format(simulations[i][5:]), color=colors[i], linewidth=2)
    else:
        plt.plot(zf, res4[i], label='EC', color=colors[i], linewidth=2)
        # plt.errorbar(cumsum4[i][0], cumsum4[i][1], linestyle='--', yerr=poisson4[i],
        #              label=' {} '.format(simulations[i]), color=colors[i], linewidth=2)
        plt.plot(cumsum4[i][0], cumsum4[i][1], linestyle='--', alpha=1, label=' {}'.format(simulations[i]),
                 color=colors[i], linewidth=2)
        plt.fill_between(cumsum4[i][0], cumsum4[i][1] - poisson4[i],cumsum4[i][1] + poisson4[i],  color=colors[i],alpha=0.2)
plt.xlabel('z ', size=20)
plt.xlim(0.01, 1.5)
plt.legend()
# if diff:
#     plt.ylabel('dP/dz', size=20)
# else:
#     plt.ylabel('P($Z_{50} > z$)', size=20)
if corr:
    plt.title('with infall {:2.1e}<M<{:2.1e}'.format(Mmins[2], Mmaxs[2]))
    if diff:
        plt.savefig('dpdz_corr_{:2.1e}<M<{:2.1e}_bim.png'.format(Mmins[2], Mmaxs[2]), dpi=100, bbox_inches='tight')
    else:
        plt.savefig('z50_corr_{:2.1e}<M<{:2.1e}_bim.png'.format(Mmins[2], Mmaxs[2]), dpi=100, bbox_inches='tight')
else:
    plt.title('{:2.1e}<M<{:2.1e}'.format(Mmins[2], Mmaxs[2]))
    if diff:
        plt.savefig('dpdz_{:2.1e}<M<{:2.1e}_bim.png'.format(Mmins[2], Mmaxs[2]), dpi=100, bbox_inches='tight')
    else:
        plt.savefig('z50_{:2.1e}<M<{:2.1e}_bim.png'.format(Mmins[2], Mmaxs[2]), dpi=100, bbox_inches='tight')

plt.show()


'''masses = [1e8, 1e10, 1e12, 1e14]
zf = np.linspace(0.05, 5, 30)
dz = zf[1]-zf[0]

for mass in masses:
    prob1 = new_proba(mass, zf, acc=1000000, model='EC', colos=True)
    prob2 = new_proba(mass, zf, acc=1000000, model='press', colos=True)
    dpdz1 = (prob1[2:]-prob1[:-2])*0.5/dz
    dpdz2 = (prob2[2:]-prob2[:-2])*0.5/dz
    #plt.plot(zf, new_proba(mass, zf, acc=2000000, model='EC', colos=True), label='mass='+ str(mass))
    plt.plot(zf[1:-1], -dpdz1, '--', linewidth=3, label='SC log mass='+ str(round(np.log10(mass), 2)))
    plt.plot(zf[1:-1], -dpdz2, linewidth=2, label='SC log mass='+ str(round(np.log10(mass), 2)))
plt.legend()
plt.show()'''

'''zfs = np.linspace(0.001, 3, 50)
te1 = new_proba(zf = zfs, M=1e11, frac=0.3, acc=500000, model='EC', colos=True)
te2 = new_proba(zf = zfs, M=1e11, frac=0.15, acc=500000, model='EC', colos=True)
te3 = new_proba(zf = zfs, M=1e11, frac=0.3, acc=500000, model='press', colos=True)
plt.plot(zfs, te1, label = 'EC 0.3')
plt.plot(zfs, te2, label = 'EC 15')
plt.plot(zfs, te3, label = 'press 0.3')
plt.legend()
plt.show()'''


def proba2(wf, a, man=False, acc=1000):
    if man == True:
        xs = np.logspace(-10, 0, acc)
        Ks = K(xs, wf)
        mus = mu(xs, a)
        dx = (xs[2:] - xs[:-2]) * 0.5
        return -np.sum(Ks[1:-1] * mus[1:-1] * dx)
    else:
        def f(x):
            return K(x, wf) * mu(x, a)

        return -quad(f, 0, 1)[0]


def dpdw(wf, a, man=False, acc=1000):
    if man == True:
        xs = np.logspace(-10, 0, acc)
        newpar = 1 / wf - wf / xs
        Ks = K(xs, wf)
        mus = mu(xs, a)
        dx = (xs[2:] - xs[:-2]) * 0.5
        return -np.sum(Ks[1:-1] * mus[1:-1] * newpar * dx)
    else:
        def f(x):
            return K(x, wf) * mu(x, a) * (1 / wf - wf / x)

        return -quad(f, 0, 1)[0]


'''wf = np.linspace(0, 4, 1000)
res = []
res2 = []
for el in wf:
    res.append(proba2(el, man = False, acc=1000, a=-2))
    res2.append(dpdw(el, man = False, acc=1000, a=1))
res = np.array(res)
#dpdw = (res[2:] - res[:-2])/(wf[2:] - wf[:-2])
plt.plot(wf, res2)
#plt.plot(wf, -res)
plt.show()'''

'''zs = np.linspace(0.1, 2, 500)
masses = [1e8, 1e11, 1e14]
for ms in masses:
    res = new_proba(ms, zf=zs, acc=5000, colos=True, model="press", A=0.5, a=0.707, p=0)
    dpdw = (res[2:] - res[:-2])/(zs[2:] - zs[:-2])
    #plt.plot(zs[1:-1], -dpdw, label='log M='+str(np.log10(ms)), linewidth=2.5)
    plt.plot(zs, res, label='log M='+str(np.log10(ms)))
plt.legend(fontsize='xx-large', fancybox=True)
plt.xlabel('z', size=25)
plt.ylabel('$P(z_f>z)$', size=20)
#plt.ylabel('$dP/dz$', size=20)
plt.xticks(size=18)
plt.yticks(size=18)
plt.show()'''

'''zi = [0, 1, 2]
s8=0.4
om0 = 0.7
Mass = 1e13
for red in zi:
#    zs = np.linspace(red -0.1+ 1.2*s8/(0.2*np.log10(Mass) +2*om0+ np.exp(red)), 3, 1000)
    zs = np.linspace(red + 1.2*s8/(2.7+ 0.2*np.log10(Mass) + 0.1*om0), 4, 1000)
    res = proba(M=Mass, sig8=s8, om0=om0, zi=red, zf=zs, acc=1000, colos=True)
    dpdw = (res[2:] - res[:-2])/(zs[2:] - zs[:-2])
    plt.plot(zs[1:-1], -dpdw, label='$z_i=$'+str(red))
    #plt.plot(zs, res, label='$z_i=$'+str(red))
plt.legend()
plt.xlabel('z', size=15)
#plt.ylabel('$P(z_f>z)$', size=15)
plt.ylabel('$dP/dz$', size=15)
plt.show()'''


def median_formation(M, z, frac=0.5, acc=1000, nzeds = 10000, sig8=sigma8, h=h, kmax=30, window='TopHat', prec=1000,
                     om0=om, ol0=oml, omb=omb, model='EC', camb=False, colos=True, outc=False):
    zs = np.linspace(z + 0.1, 6 + z, nzeds)
    res = new_proba(M, zs, frac, acc, z, sig8, h, kmax, window, prec, om0, ol0, omb, camb, model, colos)
    zf = np.max(zs[res > 0.5])
    if outc:
        return 0.7 + 0.77 * np.log10(zf)
    else:
        return zf


def average_formation(M, z, frac=0.5, acc=1000, nzeds = 10000, sig8=sigma8, h=h, kmax=30, window='TopHat', prec=1000,
                      om0=om, ol0=oml, omb=omb, model='EC', camb=False, colos=False, outc=False):
    zs = np.linspace(z + 1.2 * sig8 / (2.7 + 0.2 * np.log10(M) + 0.1 * om0), z + 8, nzeds)
    res = new_proba(M, zs, frac, acc, z, sig8, h, kmax, window, prec, om0, ol0, omb, camb, model, colos)
    dens = (res[2:] - res[:-2]) / (zs[2:] - zs[:-2])
    dz = zs[1] - zs[0]
    lower = -dz * np.sum(zs[1:-1] * dens)
    deltap = (zs[0] - z) * dens[0]
    upper = lower - deltap
    if outc:
        return 0.7 + 0.77 * np.log10(lower)
    else:
        return [lower, upper]


def peak_formation(M, z, frac=0.5, acc=1000, nzeds = 10000, sig8=sigma8, h=h, kmax=30, window='TopHat', prec=1000,
                   om0=om, ol0=oml, omb=omb, model='EC', camb=False, colos=False, outc=False):
    zs = np.linspace(z + 0.1, z + 6, nzeds)
    res = new_proba(M, zs, frac, acc, z, sig8, h, kmax, window, prec, om0, ol0, omb, camb, model, colos)
    dens = -(res[2:] - res[:-2]) / (zs[2:] - zs[:-2])
    zf = zs[np.argmax(dens)]
    if outc:
        return 0.7 + 0.77 * np.log10(zf)
    else:
        return zf


def slope_age(z, which_formation='median', frac=0.5, acc=1000, sig8=sigma8, h=h, kmax=30, window='TopHat', prec=1000,
              om0=om, ol0=oml, omb=omb, model='EC', camb=False, colos=True):
    if which_formation == 'median':
        zf1 = median_formation(1e8, z, frac, acc, sig8, h, kmax, window, prec, om0, ol0, omb,
                               model, camb, colos)
        zf2 = median_formation(1e14, z, frac, acc, sig8, h, kmax, window, prec, om0, ol0, omb,
                               model, camb, colos)
        return (zf1 - zf2) / 6
    elif which_formation == 'peak':
        zf1 = peak_formation(1e8, z, frac, acc, sig8, h, kmax, window, prec, om0, ol0, omb,
                             model, camb, colos)
        zf2 = peak_formation(1e14, z, frac, acc, sig8, h, kmax, window, prec, om0, ol0, omb,
                             model, camb, colos)
        return (zf1 - zf2) / 6
    elif which_formation == 'average':
        zf1 = average_formation(1e8, z, frac, acc, sig8, h, kmax, window, prec, om0, ol0, omb,
                                model, camb, colos)[0]
        zf2 = average_formation(1e14, z, frac, acc, sig8, h, kmax, window, prec, om0, ol0, omb,
                                model, camb, colos)[0]
        return (zf1 - zf2) / 6


'''zi = np.linspace(0, 2, 20)
mass = [3e10, 1e12, 5e13]
for m in mass:
    res = []
    for red in zi:
        res.append(median_formation(M=m, z=red, colos=True)-red)
        #plt.plot(zs[1:-1], dpdw)
    plt.plot(zi, res, label='M='+str(m))
plt.legend()
plt.xlabel('z')
plt.ylabel('$z_f$')
plt.show()'''

'''#s8 = [0.6, 0.8, 1]
reds = [0]
mass = np.logspace(10, 14, 20)
for red in reds:
    res = []
    for el in mass:
        res.append(average_formation(M=el/h, frac=0.4,  z=red, sig8 = sigma8, colos=True)[0])
        #plt.plot(zs[1:-1], dpdw)
    plt.plot(mass, res, label='z = '+str(red))
#y = -0.23*np.log10(mass/1e12) +2.5
#plt.plot(mass, y, label = 'Fit formula')
plt.legend()
plt.xlabel('$M$', size=15)
plt.xscale('log')
plt.ylabel('$1+z_{formation}$', size=15)
plt.xlim(1e10, 1e14)
plt.legend()
plt.show()'''

'''mass = np.logspace(9, 15, 20)
#omv = [0.15, 0.3, 0.7]
omv = [0.3]
linsetyles = ['-', '--', '-.']
for i in range(len(omv)):
    res1=[]
    res2=[]
    res3=[]
    for el2 in mass:
        res1.append(peak_formation(M=el2, z=0, om0=omv[i], colos=True))
        res2.append(median_formation(M=el2, z=0, om0=omv[i], colos=True))
        res3.append(average_formation(M=el2, z=0, om0=omv[i], colos=True))
    plt.plot(mass, res1, color='green', linestyle=linsetyles[i], label='Peak $\Omega_m=$'+str(omv[i]))
    plt.plot(mass, res2, color='orange', linestyle=linsetyles[i], label='Median $\Omega_m=$'+str(omv[i]))
    plt.plot(mass, res3, color='blue', linestyle=linsetyles[i], label='Average $\Omega_m=$'+str(omv[i]))

plt.legend()
plt.xlabel('$M$', size=15)
plt.xscale('log')
plt.ylabel('$z_{formation}$', size=15)
plt.show()'''

'''mass = np.logspace(8, 11, 10)
s8 = [0.5, 0.8, 1.1]
oms = [0.1, 0.3, 0.6]
linsetyles = ['-', '--', '-.']
for i in range(len(s8)):
    res1=[]
    res2=[]
    res3=[]
    for el2 in mass:
        res1.append(peak_formation(M=el2, z=0, sig8=s8[i],  colos=True))
        res2.append(median_formation(M=el2, z=0, sig8=s8[i], colos=True))
        res3.append(average_formation(M=el2, z=0,sig8=s8[i], colos=True))
    plt.plot(mass, res1, color='green', linestyle=linsetyles[i], label='Peak $\sigma_8=$'+str(oms[i]))
    plt.plot(mass, res2, color='orange', linestyle=linsetyles[i], label='Median $\sigma_8=$'+str(oms[i]))
    plt.plot(mass, res3, color='blue', linestyle=linsetyles[i], label='Average $\sigma_8=$'+str(s8[i]))

plt.legend()
plt.xlabel('$M$', size=15)
plt.xscale('log')
plt.ylabel('$z_{formation}$', size=15)
plt.show()'''

'''zi = np.linspace(0, 1, 20)
res1 = []
res2 = []
res3 = []
for el in zi:
    res1.append(peak_formation(M=4e13, z=el, colos=True))
    res2.append(median_formation(M=4e13, z=el, colos=True))
    res3.append(average_formation(M=4e13, z=el, colos=True))
plt.plot(zi, res1, label='Maximum probability')
plt.plot(zi, res2, label='Mean')
plt.plot(zi, res3, label='Average')
plt.legend()
plt.xlabel('$z_{0}$', size=15)
plt.ylabel('$z_{formation}$', size=15)
plt.show()'''

'''s8 = np.linspace(0.5, 1.1, 20)
res = []
for el in s8:
    res.append(average_formation(M=1e12, z=0, sig8=el, colos=True))
    #plt.plot(zs[1:-1], dpdw)

plt.plot(s8, res)
plt.legend()
plt.xlabel('$\sigma_8$', size=15)
plt.ylabel('$z_{formation}$', size=15)
plt.show()'''

'''omeg = np.linspace(0.1, 0.7, 20)
res = []
for el in omeg:
    res.append(average_formation(M=1e12, z=0, om0=el, colos=True))
    #plt.plot(zs[1:-1], dpdw)

plt.plot(omeg, res)
plt.legend()
plt.xlabel('$\Omega_m$', size=15)
plt.ylabel('$z_{formation}$', size=15)
plt.show()'''

'''sze = 15
#zobs = [0, 1, 2]
zobs = [0.15]

omv = np.linspace(0.15, 0.5, sze)
s8 = np.linspace(0.6, 1.1, sze)
nom = np.zeros((sze,sze))

x = np.array([omv]*sze).transpose()
y = np.array([s8]*sze)
for el in zobs:
    for i in range(sze):
        for j in range(sze):
            nom[i,j] = peak_formation(M=4e13, z=el, om0=omv[i], sig8= s8[j], colos=True, outc=False)
    plt.contourf(x, y, nom, levels=100, cmap='jet')
    plt.xlabel('$\Omega_m$', size = 25)
    plt.ylabel('$\sigma_8$', size = 25)
    plt.title('Median formation redshift given $z_{obs} =$'+str(el))
    cbar = plt.colorbar()
    cbar.ax.tick_params(labelsize=15)
    plt.xticks(size=15)
    plt.yticks(size=15)
    plt.show()'''

'''sze = 15
#zobs = [0, 1, 2]
zobs = [0.15]

omv = np.linspace(0.15, 0.5, sze)
S8 = np.linspace(0.4, 1.4, sze)
nom = np.zeros((sze,sze))

x = np.array([omv]*sze).transpose()
y = np.array([S8]*sze)
for el in zobs:
    for i in range(sze):
        for j in range(sze):
            s8 = S8[j]*(0.3/omv[i])**0.46
            nom[i,j] = peak_formation(M=4e13, z=el, om0=omv[i], sig8= s8, colos=True, outc=True)
    plt.contourf(x, y, nom, levels=100, cmap='jet')
    plt.xlabel('$\Omega_m$', size = 15)
    plt.ylabel('$S_8$', size = 15)
    plt.colorbar()
    plt.title('Peak concentration $z_{obs} =$'+str(el))
    plt.show()'''
'''sze = 15
zobs = [0, 0.5, 1, 2]
#zobs = [0.15]

omv = np.linspace(0.15, 0.5, sze)
s8 = np.linspace(0.6, 1.1, sze)
nom = np.zeros((sze,sze))

x = np.array([omv]*sze).transpose()
y = np.array([s8]*sze)
for el in zobs:
    for i in range(sze):
        for j in range(sze):
            nom[i,j] = slope_age(z=el, om0=omv[i], sig8= s8[j], colos=True)
    plt.contourf(x, y, nom, levels=100, cmap='jet')
    plt.xlabel('$\Omega_m$', size = 15)
    plt.ylabel('$\sigma_8$', size = 15)
    plt.colorbar()
    plt.title('Slope')
    plt.show()'''

'''sze = 15
#zobs = [0, 1, 2]
zobs = [0]

omv = np.linspace(0.15, 0.5, sze)
s8 = np.linspace(0.6, 1, sze)
nom = np.zeros((sze,sze))
cref = median_formation(M=4e13, frac=0.1, z=zobs[0], om0=0.3, sig8 = 0.8, colos=True, outc=True)
clim = [cref-0.1, cref+0.1]

x = np.array([omv]*sze).transpose()
y = np.array([s8]*sze)
for el in zobs:
    for i in range(sze):
        for j in range(sze):
            val = median_formation(M=4e13, frac=0.1, z=el, om0=omv[i], sig8= s8[j], colos=True, outc=True)
            if (val < clim[1]) and (val > clim[0]):
                nom[i,j] = 10**val
            else :
                nom[i,j] = 0
    plt.contourf(x, y, nom, levels=100, cmap='jet')
    plt.xlabel('$\Omega_m$', size = 15)
    plt.ylabel('$\sigma_8$', size = 15)
    plt.colorbar()
    plt.title('Peak concentration $z_{obs} =$'+str(el))
    plt.show()'''

'''Mass = np.logspace(9, 16, 7)
for ms in Mass:
    sze = 15
    omv = np.linspace(0.25, 0.35, sze)
    s8 = np.linspace(0.7, 0.9, sze)
    nom = np.zeros((sze,sze))
    x = np.array([omv]*sze).transpose()
    y = np.array([s8]*sze)
    for i in range(sze):
        for j in range(sze):
            nom[i,j] = 10**median_formation(M=ms, z=0.15, frac=0.1, om0=omv[i], sig8= s8[j], colos=True, outc=True)
    plt.contourf(x, y, nom, levels=100, cmap='jet')
    plt.title('median $z_f$ for log M='+str(round(np.log10(ms),2))+' at z=0.15', size=15)
    plt.xlabel('$\Omega_m$', size = 15)
    plt.ylabel('$\sigma_8$', size = 15)
    plt.colorbar()
    plt.show()'''

'''reds = [1]
m = 1e13
for red in reds:
    sze = 15
    omv = np.linspace(0.2, 0.6, sze)
    s8 = np.linspace(0.6, 1.1, sze)
    nom = np.zeros((sze, sze))
    x = np.array([omv] * sze).transpose()
    y = np.array([s8] * sze)
    for i in range(sze):
        for j in range(sze):
            nom[i, j] = median_formation(M=m, z=red, frac=0.5, om0=omv[i], sig8=s8[j], acc=1000,
                                         model='SC', colos=True, outc=False)
    plt.contourf(x, y, nom, levels=100, cmap='jet')
    plt.title('Median $z_{50}$ M=' + str(round(np.log10(m), 2)) + ' z=' + str(round(red, 2)) + ' SC', size=15)
    plt.xlabel('$\Omega_m$', size=15)
    plt.ylabel('$\sigma_8$', size=15)
    plt.colorbar()
    plt.show()'''

'''r = 5000
l = 2000
zs = np.linspace(0.14, 2, l)
age = proba(4e13, zf=zs, zi = 0.1, colos=True)
rand = np.random.uniform(0,np.max(age), size=r)


mat_rand = np.array([rand]*l)  #lxr
mat_age = np.array([age]*r).transpose() #lxr
mat_zs = np.array([zs]*r).transpose()

res = np.max(mat_zs*(mat_age>mat_rand), axis=0)

plt.hist(res, histtype='step', bins=30)
plt.show()'''
