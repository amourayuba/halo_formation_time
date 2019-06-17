from __future__ import division
from colossus.cosmology import cosmology
from colossus.lss import mass_function
import numpy as np
import matplotlib.pyplot as plt
from cosmo_parameters import *
from power_spectrum_analytic import *
from growth_factor import *
from fluctuation_rms import *


cosmology.setCosmology('planck15');

def hmf(M, z=0, window='Gauss', sigma8=sigma8, om0=omega_m0, ol0=omega_l0, h=h, omb=omb):
    del_c = delta_c(z, om0, ol0)
    sig = sigma_a_M(M, window=window, z=0, sig8=sigma8, h=h, om0=om0, omb=omb)
    dlsig = np.log(sig[1:]/sig[:-1])
    dlM = np.log(M[1:]/M[:-1])
    new_sig = (sig[1:]+sig[:-1])*0.5
    new_m = (M[1:]+M[:-1])*0.5

    ra1 = np.sqrt(2/np.pi)*rho_m(z=0, om0=om0)*del_c/(new_m**2*new_sig)
    ra2 = np.exp(-del_c**2/(2*new_sig**2))
    ra3 = dlsig/dlM
    return -ra1*ra2*ra3

def fps(nu):
    return np.sqrt(2/np.pi)*nu*np.exp(-nu**2/2)

def nu(M, z=0, h=0.67, om0=omega_m0, ol0=omega_l0, omb=omb, sig8 = sigma8, win='Gauss' ):
    return delta_c(z, om0, ol0)/sigma_a_M(M, z=z, sig8=sig8, h=h, om0=om0, omb=omb, window=win)

def Mstar(lMmin=6, lMmax=15, npoints = 10000, z=0, h=0.67, om0=omega_m0, ol0=omega_l0, omb=omb, sigma8 = sigma8, win='Gauss'):
    mass = np.logspace(lMmin, lMmax, npoints)
    res = nu(mass, z=z, h=h, om0=om0, ol0=ol0, omb=omb, sig8 = sigma8, win='Gauss' )
    return np.min(mass[res>1])



'''M = np.logspace(11,15, 100)
z = [0,0.5,1,2]
for el in z:
    y1 = hmf(M, z=el, sigma8=0.8)
    plt.loglog(M[1:], -y1, label='z='+str(el))
plt.xlabel('M [$h^{-1}M_\odot$]', size = 15)
plt.ylabel('n(M) [$h^4/Mpc^{3}/M_\odot$]', size = 15)
plt.title('Press and Schechter halo mass function', size = 15)
plt.legend()
plt.show()'''

'''sigma8 = [0.6,0.7,0.8,0.9,1,1.1]
for el in sigma8:
    y1 = hmf(M, z=0, sigma8=el)
    plt.loglog(M[1:], -y1, label='$\sigma_8=$'+str(el))
plt.xlabel('M [$h^{-1}M_\odot$]', size = 15)
plt.ylabel('n(M) [$h^4/Mpc^{3}/M_\odot$]', size = 15)
plt.title('Press and Schechter halo mass function', size = 15)
plt.legend()
plt.show()'''


'''om1 = [0.2,0.3,0.4,0.5]
for el in om1:
    y1 = hmf(M, z=0, sigma8=0.8, om0=el)
    plt.loglog(M[1:], -y1, label='$\Omega_m=$'+str(el))
plt.xlabel('M [$h^{-1}M_\odot$]', size = 15)
plt.ylabel('n(M) [$h^4/Mpc^{3}/M_\odot$]', size = 15)
plt.title('Press and Schechter halo mass function', size = 15)
plt.legend()
plt.show()'''


def cumulative_hmf(M, prec = 1000, z=0, window='Gauss', sigma8=sigma8, om0=omega_m0, ol0=omega_l0, h=h):
    x = np.linspace(1, M, prec)
    dx = M/prec
    return np.sum(hmf(x, z, window, sigma8, om0, ol0, h, om))*dx

def cumulative_hmf_log(M, prec = 100, z=0, window='Gauss', sigma8=sigma8, om0=omega_m0, ol0=omega_l0, h=h):
    lm = np.log10(M)
    x = np.logspace(1, lm, prec)
    dlnx = lm/prec
    return np.sum(hmf(x, z, window, sigma8, om0, ol0, h, om)*x[1:])*dlnx

def integrated_hmf(lMmin, lMmax, prec = 100, z=0, window='Gauss', sigma8=sigma8, om0=omega_m0, ol0=omega_l0, h=h):
    x = np.logspace(lMmin, lMmax, prec)
    dlnx = (lMmax-lMmin)/ prec
    return np.sum(hmf(x, z, window, sigma8, om0, ol0, h, om) * x[1:]) * dlnx



############################----------------------------PLOTS OF VARIOUS QUANTITIES------------###############


###################-----   omega_m vs sigma8 at n = const----------------############################

'''omv = np.linspace(0.01, 0.5, 30)
olv = 1-omv
#ombv = 0.13*omv
sig8 = np.linspace(0.1, 1.5, 30)
nom = np.zeros((30,30))
mt = np.logspace(13,16, 100)
for i in range(30):
    for j in range(30):
        nom[i,j] = np.sum(hmf(mt, sigma8=sig8[j], om0=omv[i], ol0=olv[i],omb=ombv[i]))#nom[i,j] = integrated_hmf(1, 16, prec = 50, sigma8=sig8[j], om0=omv[i])
plt.contourf(omv, sig8, np.log(nom+1), levels=30, cmap='RdGy')
plt.xlabel('$\Omega_m$')
plt.ylabel('$\sigma_8$')
plt.colorbar()
plt.show()'''



'''omv = np.linspace(0.15, 0.7, 30)
olv = 1-omv
#ombv = 0.13*omv
sig8 = np.linspace(0.3, 1.2, 30)
nom = np.zeros((30,30))
mt = np.logspace(8,16, 100)
for i in range(30):
    for j in range(30):
        nom[i,j] = np.sum(fps(nu(mt, sig8=sig8[j], om0=omv[i], ol0=olv[i])))#nom[i,j] = integrated_hmf(1, 16, prec = 50, sigma8=sig8[j], om0=omv[i])
plt.contourf(omv, sig8, np.log(nom+1), levels=10, cmap='RdGy')
plt.xlabel('$\Omega_m$', size = 15)
plt.ylabel('$\sigma_8$', size = 15)
plt.colorbar()
plt.show()'''

###################----- Dependence on redhsift----------------############################


'''z = [0, 1, 2, 4]
mt = np.logspace(11,16, 100)
for el in z:
    res = hmf(mt, sigma8=0.8, window = 'TopHat', z=el)
    plt.loglog(mt[1:], res, label = 'z = %.f' % (el))
plt.xlim(2e11, 5e15)
plt.ylim(1e-25, 1e-12)
plt.legend()
plt.show()'''

###################------------------Comparison with colossus-----------------------############################


'''M = 10**np.arange(11.0, 15.5, 0.1)
plt.figure()
plt.xlabel('Mass')
plt.ylabel('f')
plt.loglog()
plt.xlim(1E11, 2E15)
plt.ylim(1E-2, 1E0)
mfunc = mass_function.massFunction(M, z=0, mdef = 'fof', model = 'press74', q_out = 'f')
res = fps(nu(M, z=0, sig8=0.8159, om0=0.3089, omb=0.0486, h=0.68, win='TopHat'))
res2 = fps(nu(M, z=0, sig8=0.8159, om0=0.3089, omb=0.0486, h=0.68, win ='Gauss'))
res3 = fps(nu(M, z=0, sig8=0.8159, om0=0.3089, omb=0.0486, h=0.68, win ='k-Sharp'))
plt.plot(M, mfunc, color = 'green',label='Colossus')
plt.plot(M, res, color = 'black', label = 'Yuba Analytic Top Hat')
plt.plot(M, res2, color = 'red', label = 'Yuba Analytic Gaussian')
plt.plot(M, res3, color = 'blue', label = 'Yuba Analytic K-Sharp')
plt.legend()
plt.show()'''



###################"------------------------Plotting M_\star----------------#####################################

'''z = np.linspace(0, 4, 50)
res = []
for el in z:
    res.append(Mstar(z=el, npoints=1000))
plt.plot(z, res)
plt.yscale('log')
plt.xlabel('z', size = 15)
plt.ylabel('$M^\star$[$h^{-1}M_\odot$]', size = 15)
plt.xlim(0, 4)
plt.ylim(1e8, 1e13)
plt.title('Press and Schechter caracteristic non linear mass', size=15)
plt.show()'''


'''om = np.linspace(0.1, 0.6, 50)
res = []
for el in om:
    res.append(Mstar(z=0, om0=el, ol0=1-el, npoints=100))
plt.plot(om, res)
plt.yscale('log')
plt.xlabel('$\Omega_m$', size = 15)
plt.ylabel('$M^\star$[$h^{-1}M_\odot$]', size = 15)
plt.xlim(0.1, 0.6)
plt.ylim(1e6, 1e15)
plt.title('Press and Schechter caracteristic non linear mass', size=15)
plt.show()'''


'''s8 = np.linspace(0.1, 1.5, 50)
res = []
for el in s8:
    res.append(Mstar(z=0, sigma8=el, npoints=1000))
plt.plot(s8, res)
plt.yscale('log')
plt.xlabel('$\sigma_8$', size = 15)
plt.ylabel('$M^\star$[$h^{-1}M_\odot$]', size = 15)
plt.xlim(0.5, 1.2)
plt.ylim(2e10, 5e14)
plt.title('Press and Schechter caracteristic non linear mass', size=15)
plt.show()'''


'''omv = np.linspace(0.01, 0.7, 30)
sig8 = np.linspace(0.1, 1.5, 30)
nom = np.zeros((30,30))
for i in range(30):
    for j in range(30):
        nom[i,j] = Mstar(lMmin=1, lMmax=18,  z=0, om0 = omv[i], ol0= 1 - omv[i], sigma8=sig8[j], npoints=100)
plt.contourf(omv, sig8, np.log10(nom+1), levels=50, cmap='RdGy')
plt.xlabel('$\Omega_m$', size = 15)
plt.ylabel('$\sigma_8$', size = 15)
plt.colorbar()
plt.title('$\log M^\star$')
plt.show()'''