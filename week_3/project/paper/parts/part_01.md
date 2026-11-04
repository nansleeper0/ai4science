# Часть 1: с. 1–2

[с. 1]
MNRAS 000, 1–9 (2023) Preprint 8 April 2024 Compiled using MNRAS L ATEX style file v3.0
Flickering pulsations in bright X-ray pulsars:
the evidence of gravitationally lensed and eclipsed accretion column
Alexander A. Mushtukov1⋆, Albert Weng2†, Sergey S. Tsygankov3, Ilya A. Mereminskiy4
1Astrophysics, Department of Physics, University of Oxford, Denys Wilkinson Building, Keble Road, Oxford OX1 3RH, UK
2Fairmont Preparatory Academy, 2200 W Sequoia Ave, Anaheim, CA 92801, USA
3Department of Physics and Astronomy, FI-20014 University of Turku, Finland
4Space Research Institute, Russian Academy of Sciences, Profsoyuznaya 84/32, 117997 Moscow, Russia
8 April 2024
ABSTRACT
It is expected that extreme mass accretion rate onto strongly magnetised neutron star results in appearance of
accretion columns above stellar surface. For a distant observer, rotation of a star results in periodic variations of
X-ray flux. Because the mass accretion rate fluctuates around the average value, the pulse profiles are not stable
and demonstrate fluctuations as well. In the case of bright X-ray pulsars, however, pulse fluctuations are not solely
attributed to variations in the mass accretion rate. They are also influenced by the variable height of the columns,
which is dependent on the mass accretion rate. This study delves into the process of pulse profile formation in bright
X-ray pulsars, taking into account stochastic fluctuations in the mass accretion rate, the corresponding variations in
accretion column geometry and gravitational bending. Our analysis reveals that potential eclipses of accretion columns
by a neutron star during their spin period should manifest specific features in pulse profile variability. Applying a
novel pulse profile analysis technique, we successfully detect these features in the bright X-ray transient V 0332+53
at luminosities ≳2×1038erg s−1. This detection serves as compelling evidence for the eclipse of an accretion column
by a neutron star. Detection of the eclipse places constraints on the relation between neutron star mass, radius and
accretion column height. Specifically, we can establish an upper limit on the accretion column height, which is crucial
for refining theoretical models of extreme accretion.
Key words: accretion – accretion discs – X-rays: binaries – stars: neutron – stars: oscillations
1 INTRODUCTION
Accreting strongly magnetised neutron stars (NSs) man-
ifest themselves as X-ray pulsars (XRPs, see Mushtukov &
Tsygankov 2022 for review). Magnetic field ( B-field) at the
NS surface in XRPs is typically ≳1012G. Strong field of a NS
disturbs accretion flow at distance ∼107−108cm, which is
called the magnetospheric radius, and shapes the geometry of
accretion flow within it directing material towards small re-
gions located near the magnetic poles of a NS. Accretion flow
is inevitably decelerated at the NS surface or in close prox-
imity to the surface. The geometry of the emitting region
depends on the mass accretion rate. In the case of relatively
low mass accretion rates (sub-critical regime, ≲1017g s−1),
the flow reaches the stellar surface and is decelerated in the
atmosphere of a NS (Zel’dovich & Shakura 1969), which re-
sults in hot spot geometry of the emitting regions. At high
mass accretion rates (super-critical regime, ≳1017g s−1), the
dynamics of accretion flow is affected by the radiation pres-
sure and the flow is decelerated in radiation dominated shock
⋆E-mail: alexander.mushtukov@physics.ox.ac.uk (AAM)
†E-mail: albertweng1213@gmail.com (AW)above NS surface (Basko & Sunyaev 1976; Wang & Frank
1981; Mushtukov et al. 2015b; Abolmasov & Lipunova 2023).
Shock wave above the surface and the sinking region below
it form an accretion column - structure supported by the ra-
diation pressure and confined by extremely strong magnetic
field. The accurate numerical model of accretion columns is
still developing and requires accounting for many aspects, in-
cluding magneto-hydrodynamics (Sheng et al. 2023), radia-
tive transfer in a strong magnetic field (see Meszaros 1992
for review, and Suleimanov et al. 2022 for the recent results)
and possibly energy losses due to creation of electron-positron
pairs and further neutrino emission (Mushtukov et al. 2018c,
2019a; Asthana et al. 2023).
The formation mechanism of the beam pattern is antici-
pated to differ between sub-critical and super-critical XRPs
(Gnedin & Sunyaev 1973). In the sub-critical regime, a ma-
jority of X-ray photons originate from hot spots, whose ge-
ometry exhibits only marginal dependence on the mass ac-
cretion rate. Conversely, in the super-critical regime, photons
are emitted by the walls of the accretion column, where the
column height correlates with the mass accretion rate (Basko
& Sunyaev 1976) and is contingent on the strength of the neu-
©2023 The AuthorsarXiv:2404.04137v1  [astro-ph.HE]  5 Apr 2024

[с. 2]
2A. Mushtukov et al.
tron star’s magnetic field (Mushtukov et al. 2015b). A frac-
tion of the X-ray radiation emitted by the columns is inter-
cepted and reprocessed by the atmosphere of a NS (Poutanen
et al. 2013; Postnov et al. 2015). Thus, in the case of super-
critical accretion, a distant observer detects a combination of
direct flux from the accretion column and flux reflected by
the neutron star (see Fig. 1). Both components of the pat-
tern undergo gravitational light bending in the vicinity of a
NS (Riffert & Meszaros 1988; Kraus 2001; Mushtukov et al.
2018b; ?).
Mass accretion rate in all X-ray binaries, including XPRs,
is known to be fluctuating on different time scales. In partic-
ular, variations of the mass accretion rate can be generated
in accretion disc due to the stochastic nature of viscosity
(Lyubarskii 1997; Mushtukov et al. 2019b). The viscosity in
the accretion disc can be caused by magnetic dynamo that
generates a poloidal magnetic field component in a random
fashion (Balbus & Hawley 1991; Brandenburg et al. 1995).
The process is stochastic by its nature and results in viscosity
fluctuations on time scales close to the local dynamical time
scales. The local viscosity fluctuations result in local fluctua-
tions of the mass accretion rate at the inner disc radius and,
further, at the NS surface. Fluctuations in the mass accretion
rate onto the NS surface give rise to variations in accretion
luminosity, observable as fluctuations in X-ray energy flux by
a distant observer. In the case of super-critical XRPs with
accretion columns, fluctuating mass accretion rates induce
variations in the emission region geometry — specifically, the
accretion column height and the illuminated fraction of a NS
surface. The dynamic changes in the emission region geom-
etry, along with the corresponding fluctuations in the beam
pattern, naturally contribute to additional stochastic vari-
ability in X-ray energy flux. The relative fluctuations in X-ray
energy flux depend on the observer’s viewing angle, resulting
in an anticipated phase-dependent variability in X-ray flux.
While phase-dependent relative root mean square (rms) of
a pulse profile has been previously observed in super-critical
XRPs (Tsygankov et al. 2007), it has yet to be fully explained.
In this paper, we investigate how fluctuations of accretion
column geometry affects fluctuations of X-ray energy flux
and pulse profile stability in super-critical XRPs. To test out
theoretical model, we analyze fluctuations of pulse profile in
bright X-ray transient V 0332+53 in super-critical regime of
accretion. Magnetic field at the NS surface in V 0332+53
(∼3×1012G) is known from detected cyclotron scattering
feature at ∼30 keV and its harmonics (Pottschmidt et al.
2005). Variations of cyclotron line centroid energy provide an
evidence of accretion column existence at L > 1037erg s−1
(Tsygankov et al. 2006) and transition to the super-critical
regiome of accretion at ∼1037erg s−1(Doroshenko et al.
2017).
2 MODEL SET UP
2.1 Geometry of the emitting region
We focus on XRPs in at super-critical regime of accretion
(˙M≳1017g s−1) when X-ray photons are produced by ac-
cretion columns. We assume that a NS has a spherical shape,
which is a good approximation for slowly rotating ( P≳0.1 s)
NSs. The columns above the poles of a star are modeled by
observer
Figure 1. Schematic illustration of the emission region geometry
in super-critical XRP considered in the paper. X-ray photons are
initially produced by extended accretion column. A fraction of X-
ray radiation is intercepted by a NS and reflected/reprocessed by
the atmosphere. The flux detected by a distant observer is com-
posed of direct flux from the columns and the flux reflected by
the atmosphere. Both direct and reflected components are sub-
jects of gravitational bending. Rotation geometry in the observers
reference frame is determined by the inclination of a NS iand the
magnetic obliquity θB.
cylinders of a given height H≲Rand radius rc. Accretion
column height is assumed to the related to accretion lumi-
nosity Land surface magnetic field strength (see, e.g., Mush-
tukov et al. 2015b and Fig. 3):
L∼2×1039κT
κ⊥
fH
R
erg s−1, (1)
where κT≈0.34 cm g−1is the Thomson electron scattering
opacity, κ⊥is the scattering opacity in a strong magnetic field
in the direction orthogonal to the field lines, and
f(x)≡ln(1 + x)−x
1 +x. (2)
The brightness distribution over the column height is de-
scribed by the function g(h). In this paper, we assume that
the brightness of the accretion column is homogeneously dis-
tributed over the height, i.e. g(h) = constant. The photons
leaving the walls of the column are beamed towards the NS
surface due to the scattering by free-falling material (see, e.g.
Kaminker et al. 1976; Lyubarskii & Syunyaev 1988; Poutanen
et al. 2013). The radiation energy from a unit surface area
located at the height hinto the unit solid angle of the direc-
tion ( α, ϕ) is given by Foutf(α, ϕ)g(h), where Foutis the the
flux leaving the accretion column wall. Following Poutanen
et al. 2013 we describe the angular distribution of X-ray flux
at the walls of accretion columns as
f(α, ϕ)∝3D4
7πγ(1 + 2 Dsinαcosϕ) sin2αcosϕ (3)
where β=v/cis the dimensionless velocity in units of the
speed of light, γ= (1−β2)−1/2is the Lorentz factor, and
D= [γ(1−βcosα)]−1is the Doppler factor. In this paper,
we consider a limiting case of free-fall velocity β=βff=
(RSh/(R+h))1/2, where RSh= 2GM/c2≃2.95×105cm is
the Schwarzschild radius.
Due to a strong beaming of accretion column radiation
towards the NS surface, a large fraction of X-ray photons can
be intercepted and reprocessed by the atmosphere of a NS.
MNRAS 000, 1–9 (2023)
