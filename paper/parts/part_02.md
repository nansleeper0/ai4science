# Часть 2: с. 3–5

[с. 3]
Pulse profiles fluctuations 3
time
Flux
rms
column 
e
c
l
i
p
s
e
Figure 2. The anticipated behavior of X-ray energy flux (averaged over many spin periods, denoted by the black line, and the actual flux
represented by the grey line) and the phase-resolved rms of X-ray flux (depicted by the red dotted line) during the eclipse of an accretion
column by a NS. During the column eclipse, a drop in X-ray flux is expected. Immediately before and after the eclipse, the direct flux
from the accretion column is gravitationally lensed by the NS and may exhibit significant fluctuations, even under conditions of small
variations in the mass accretion rate and the corresponding height/luminosity of the accretion column.
The process of X-ray reflection can be affected by the local
magnetic field of a NS, but it is poorly investigated up to date.
To model the reflection process, we assume that the intensity
of reflected radiation is independent on the direction, i.e. the
flux of reflected photons
Fref∝cosθref, (4)
where θrefis the angle between the direction of reflection and
local normal to the NS surface. The flux of the reprocessed
radiation is assumed to be equal to the flux locally absorbed
by the atmosphere.
A distant observer detects a flux composed of two com-
ponents: the direct flux from accretion columns and the flux
intercepted and reprocessed by the NS surface (see Fig. 1).
Both components of X-ray flux are subject of gravitational
bending in a space curved by a NS. We assume that the space
around a neutron star is described by the Schwarzschild met-
ric. This is a good approximation for neutron stars in XRPs,
where the rotation periods of a neutron star are usually longer
than 0 .1 s. Photon trajectories in the Schwarzschild metric are
flat. We describe photon trajectory in polar coordinates r≥0
andφ∈[0,2π]. The trajectory of a photon is described by
the second order differential equation (Misner et al. 1973):
d2u
dφ2= 3u2−u, (5)
where u= 0.5RSh/ris the compactness of a central object.
2.2 Mass accretion rate variability
The mass accretion rate at the magnetospheric radius expe-
riences stochastic fluctuations. The fluctuations of the mass
accretion rate in X-ray binaries are caused by clumpiness of
00.20.40.60.81
1036103710381039H/R
Luminosity, erg s-100.20.40.60.81
1036103710381039H/R
Luminosity, erg s-1Figure 3. Approximate dependencies of relative accretion column
height on the accretion luminosity calculated according (1) under
the assumption κ⊥/κT= 0.5,1,2 (from left to right). The black
dot shows the expected value of the critical luminosity (Mushtukov
et al. 2015a). The gray region corresponds to accretion columns
heights ruled out by our observational results.
the stellar wind (Walter & Zurita Heras 2007) or viscosity
fluctuations in accretion disc (Lyubarskii 1997). In the case
of accretion from the disc, each radial coordinate produces
fluctuation of a certain frequency. The frequency of locally
produced fluctuations is expected to be close to the local Ke-
plerian frequency (King et al. 2004)
fK=1
2πr3
GM1/2
. (6)
MNRAS 000, 1–9 (2023)

[с. 4]
4A. Mushtukov et al.
Viscosity fluctuations cause fluctuations of the mass accre-
tion rate that propagate inwards and outwards (Mushtukov
et al. 2018a) modulating fluctuations at other radial coordi-
nates. The fluctuations of the highest Fourier frequency are
generated close to the inner radius of accretion disc
Rm= 1.8×108ΛB4/7
12˙M−2/7
17m−1/7R12/7
6cm, (7)
where B12is the magnetic field strength at the magnetic poles
of a NS in units of 1012G,˙M17is the mass accretion rate in
units of 1017g s−1,mis a mass of a NS in units of solar
masses, R6is the NS radius in units of 106cm and Λ is a
dimensionless coefficient, which is typically taken to be Λ =
1 for the case of accretion from the wind and Λ = 0 .5 for
the case of accretion from the disc (Ghosh & Lamb 1978,
1979). Thus, the highest Fourier frequency generated in the
accretion disc is expected to be
fK,max∼0.5 Λ−3/2B−6/7
12L3/7
37m2/7R−15/7
6 Hz. (8)
According to the propagating fluctuations model applied to
the case of XRPs (Mushtukov et al. 2019b) and observational
results (Revnivtsev et al. 2009; M ¨onkk¨onen et al. 2022), the
power density spectra of stochastic fluctuations can be de-
scribed by a broken power law function with a break at fre-
quency f∼fK,max. In our simulation, we use this model
and assume that the mass accretion rate at the NS surface
replicates the fluctuations at the inner disc radius.
2.3 Neutron star rotation
NS rotation is described by two parameters: NS inclination
i(the angle between the line of sight and the rotational axis)
and the magnetic obliquity θB(the angle between the mag-
netic and rotational axis, see Fig. 1). The variations of the
angle between the line of sight and magnetic field axis ψis
described by
cosψ= sin isinθBcosφp+ cos icosθB, (9)
where φp∈[0,2π) is the phase angle of pulsations. Typically,
the angles iandθBare unknown, but the recent detection
of X-ray polarisation variability in XRPs provides an oppor-
tunity to probe the rotation geometry (see, e.g., Doroshenko
et al. 2022; Tsygankov et al. 2022, 2023; Mushtukov et al.
2023; Suleimanov et al. 2023; Malacaria et al. 2023). Re-
sults obtained with the IXPE mission (Weisskopf et al. 2022)
demonstrate that the rotation axis of NS in XRPs tends to
be orthogonal to the orbital plane of a binary system and,
probably, to accretion disc plane.
3 NUMERICAL MODEL
In our simulations, we fix the mass and radius of a NS
atM= 1.4M⊙andR= 12 km respectively. The relation
between accretion column height and luminosity is described
by approximate equation (1). Our numerical calculations are
divided into a few steps:
(i) Following the algorithms described in ?, we get the angu-
lar distributions of X-ray energy flux for different heights
Hof accretion column and, therefore, accretion luminosi-
ties. The considered range of accretion column height is
0.05R < H < R , and to calciulate a database of flux an-
gular distribution we take 100 height values within theconsidered interval. Calculating angular distribution, we
account both for direct and reflected flux of accretion col-
umn. Angular distributions of X-ray energy flux for vari-
ous heights of accretion column and luminosities are tab-
ulated.
(ii) On the base of the assumed power density spectra (PDS)
of the mass accretion rate variability and following the al-
gorithm described by Timmer & Koenig 1995, we simulate
a time series ˙M(t) that describes mass accretion rate fluc-
tuations.
(iii) The simulated time series ˙M(t) is transformed into a time
series for accretion luminosity L(t) = GM ˙M(t)/Rand
accretion column height H(t) according to (1).
(iv) On the base of time series obtained at step (iii) and inter-
polating between the angular distributions of X-ray energy
flux calculated in step (i) we get a set of time series of X-
ray flux variability in different directions with respect to
the NS magnetic axis.
(v) Using the parameters of NS rotation iandθBin the ob-
server’s reference frame, we get a model of a pulse profile
F(t, i, θ B) that fluctuates due to the variable total lumi-
nosity and variable geometry of the emission regions (i.e.,
accretion column and illuminated part of a NS surface).
(vi) On the base of calculated light curves F(t, i, θ B), we get
the phase-resolved average flux:
FP(t, i, θ B) =1
NN−1X
j=0F(t+jP, i, θ B), (10)
and the phase-resolved rms:
rmsP(t, i, θ B) =1
NN−1X
j=0F2(t+jP, i, θ B)−F2
P(t, i, θ B),(11)
where N≫1 is a number of spin period that covers the
simulated time series. For this paper, we have simulated
time series of 105Plong (i.e., N= 105).
4 NUMERICAL RESULTS
Both direct and reflected photons experience gravitational
bending. Due to the gravitational bending, accretion column
can illuminate more than a half of a NS surface. The ex-
amples of X-ray flux angular distributions at the infinity are
given in Fig. 4. The direct flux from accretion column can
be eclipsed by a NS for observers in certain directions (in
the case of relatively low accretion columns, see red and blue
lines in Fig. 4) or strongly amplified due to the gravitational
lensing (in the case of high accretion column, see black line
in Fig. 4). The calculations of X-ray flux distributions per-
formed for this paper are in agreement with earlier calcu-
lations reported in Mushtukov et al. 2018b and ?(see also
useful approximations proposed for gravitational bending by
Beloborodov 2002; Poutanen 2020). X-ray energy flux in a
given direction with respect to the magnetic field axis is de-
pendent both on total luminosity and specific geometry of the
emitting regions (accretion column and illuminated part of a
NS surface). The direct component of the X-ray flux is more
sensitive to the variations of accretion column height than
the reflected component (compare dotted and dashed-dotted
lines in Fig. 4).
MNRAS 000, 1–9 (2023)

[с. 5]
Pulse profiles fluctuations 5
0.1110
0 30 60 90 120 150 180H = 5km
H = 2km
H = 1kmFlux
ψ, deg
Figure 4. The angular distributions of X-ray flux (in units of
isotropic flux) in super-critical XRP with a single accretion col-
umn. The flux is composed of the direct component (dotted lines)
and the component reflected from the NS surface (dashed-dotted
lines). Black, red and blue lines demonstrate the distributions for
accretion column height H= 1,2 and 5 km respectively. One can
see that relatively low accretion columns can be eclipsed by a NS,
while high accretion column is gravitationally lensed for observers
located on the opposite side from a NS. Parameters: M= 1.4M⊙,
R= 12 km, uniform distribution of emitted flux over accretion col-
umn height.
The pulse profiles are determined by the angular distribu-
tion of X-ray flux in the NS reference frame, and NS rotation
in the reference frame of a distant observer, which is given by
the inclination iand magnetic obliquity θB(see Fig. 1). To
illustrate the relation between specific orientations of a NS
given by the angle ψ(see Fig. 1) and phase-resolved rms, we
demonstrate the pulse profiles for the case of i=θB=π/2
(see Fig., 5, 6), when the angle ψruns through all possible
values during one pulsation period.
Because of the variability in geometry of the emitting re-
gion, the rms of X-ray energy flux can be different from the
rms of the mass accretion rate. The flux variability can be
both stronger and weaker than the variability of the mass
accretion rate depending on the observer’s line of sight (see
Fig. 7). Fluctuation of reflected flux is typically weaker than
the corresponding fluctuations of the mass accretion rate
(compare dashed-dotted and solid lines in Fig. 7a). The fluc-
tuation of the direct flux tends to show larger relative rms
in comparison to the rms of mass accretion rate fluctuations
(compare dotted and solid lines in Fig. 7a). Amplification of
fluctuations by the direct component are dependent on rms
of the mass accretion rate (see Fig. 7b).
5 OBSERVATIONAL VERIFICATION
The proposed model was applied to the RXTE /PCA (Ja-
hoda et al. 1996) observations of the bright transient XRP
V 0332+53 obtained near the peak of the 2004 giant outburst.
The source is known to enter the supercritical regime of ac-
cretion in the bright state (Doroshenko et al. 2017), demon-
strating the appearance of sharp features in the pulse profilepossibly associated with the eclipses of accretion column by
NS (Mushtukov et al. 2018b).
Motivated by the similarities between the model pulse pro-
files shown in Fig. 5 and the observed ones in V 0332+53 we
extracted a number of 3-20 keV lightcurves for the source
covering a broad range of luminosities from 3 ×1037to
3×1038erg s−1(ObsIDs: 90427-01-04-01, 01-03-09, 01-02-03,
01-01-02). The bolometric fluxes (3-100 keV) were adopted
from Lutovinov et al. (2015) and rescaled to the Gaia dis-
tance of 5.6 kpc (Bailer-Jones et al. 2021). After the barycen-
tric correction, each lightcurve was then folded with a spin
period obtained for a given observation.
In Fig. 8 we show obtained pulse profiles along with the
pulse-phase resolved RMS for four observations at different
X-ray luminosities. One can see that the RMS exhibits weak
variability with the phase of pulsations at relatively low ac-
cretion luminosity (see Fig. 8c and 8d). At a high luminosity
state, the RMS shows strong phase dependence experiencing
jumps just before and right after the troughs in the X-ray
pulse profile (see Fig. 8a and 8b). The relative strength of
these jumps increases with luminosity, consistent with expec-
tations from our theoretical model (see Fig. 6b).
6 SUMMARY AND DISCUSSION
We have developed a comprehensive model for pulse profile
formation in super-critical XRPs, accounting for the aperi-
odic variability of the mass accretion rate onto the NS surface.
In our model, the flux observed by a distant observer is com-
posed of both the direct flux from the accretion column and
the flux reflected by the NS’s atmosphere (see Fig. 2). The
accretion column geometry, specifically its height in a super-
critical state, is considered to be dependent on the mass accre-
tion rate (Basko & Sunyaev 1976; Mushtukov et al. 2015b).
The height’s dependence on the mass accretion rate is cal-
culated following the model proposed in Mushtukov et al.
2015b, but qualitative results and theoretical predictions are
weakly dependent on specific features of underling theoreti-
cal model. Angular distribution of X-ray flux and pulse pro-
files were computed, incorporating gravitational light bending
based on the Schwarzschild metric, a suitable approximation
for XRPs due to their relatively slow rotation (typical spin
periods >1 s).
We simulated pulse profiles that fluctuate due to the vari-
ability of the mass accretion rate and the corresponding vari-
ability of the accretion column height (see the upper panel in
Fig. 5). Utilizing these simulated fluctuating pulse profiles, we
calculated the phase-resolved root mean square (rms) of the
X-ray energy flux (see eq. 5). Our results demonstrate that
accounting for the fluctuating geometry of the emission re-
gions (accretion columns and illuminated part of the NS sur-
face) significantly influences the variability of X-ray energy
flux, either amplifying or reducing it with respect to the vari-
ability of the mass accretion rate. Hence, variability of X-ray
energy flux in super-critical XRPs deviates from the variabil-
ity of the mass accretion rate, even in the reference frame
co-rotating with the NS. The reduction or amplification of
variability depends on the predominant source of X-ray pho-
tons. Notably, gravitational bending of the direct component
can significantly amplify fluctuations, while the flux reflected
from the NS surface exhibits reduced variability.
MNRAS 000, 1–9 (2023)
