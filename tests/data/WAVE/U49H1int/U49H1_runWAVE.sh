#!/bin/bash

#screen -d -m -S "WAVE Session" bash -c './scriptname.sh arg'
#screen -d
#screen -r 'number'


SCRIPTPATH=$(pwd)

export WAVE=/hdbuild/wave2
export EDITOR=gedit
. $WAVE/shell/set_wave_environment.sh

cd $SCRIPTPATH

# get current path

echo $SCRIPTPATH

# 1D Scan over energy

# Overall file name

#ONAME=U95halbe70mmEH3FULL
ONAME=U49

# folder for all ray-files ($ONAME/$RAYFILES)
RAYFILES="allrayfiles"

# First save corresponding Standard Wave-File

cp wave_U49.in wavePreScan.in

# Prepartion of results collection

RFILE="$SCRIPTPATH/Results.dat"

echo $RFILE

touch $RFILE

HEADER_RFILE="set_energy	fo_energy	fo_flux	fm_energy	fm_flux	bo_energy	bo_flux	max_energy_emittance	flux_emittance	power_all	power_sum"

echo "${HEADER_RFILE}" | tee $RFILE
# echo "${HEADER_RFILE}" | tee $ONAME/$RFILE

# Set single Parameters
# Pinhole
S_PINW="PINW=0.002"
S_PERL="s/PINW=0.002/$S_PINW/g"
perl -pi -e $S_PERL wavePreScan.in
S_PINH="PINH=0.002"
S_PERL="s/PINH=0.002/$S_PINH/g"
perl -pi -e $S_PERL wavePreScan.in
S_PINCEN1="PINCEN\(1\)=10."
S_PERL="s/PINCEN\(1\)=10./$S_PINCEN1/g"
perl -pi -e $S_PERL wavePreScan.in

#S_MPINZ="MPINZ=71"
#S_PERL="s/MPINZ=[0-9]*/$S_MPINZ/g"
#perl -pi -e $S_PERL wavePreScan.in
#S_MPINY="MPINY=71"
#S_PERL="s/MPINY=[0-9]*/$S_MPINY/g"
#perl -pi -e $S_PERL wavePreScan.in

# Harmonic
N_NHARMELL="1"
S_NHARMELL="NHARMELL=$N_NHARMELL"
S_PERL="s/NHARMELL=[0-9]*/$S_NHARMELL/g"
perl -pi -e $S_PERL wavePreScan.in

# add Harmonic to ONAME!
ONAME="${ONAME}H${N_NHARMELL}"
echo $ONAME

# Periodenlänge
S_XLELLIP="XLELLIP=0.0494"
S_PERL="s/XLELLIP=[0-9]*\.[0-9]*/$S_XLELLIP/g"
perl -pi -e $S_PERL wavePreScan.in

# Periodenanzahl
N_PERELLIP=84
S_PERELLIP="PERELLIP=$N_PERELLIP"
S_PERL="s/PERELLIP=[0-9]*\.[0-9]*/$S_PERELLIP/g"
perl -pi -e $S_PERL wavePreScan.in

# electron emmitance on/off
ELLEMM="off"
if [ "$ELLEMM" == "on" ]
then
	S_IFOLD="IFOLD=1"
	S_IBEAMFOLD="IBEAMFOLD=1"
  S_IBUNCH="IBUNCH=-1"
	S_NBUNCH="NBUNCH=1000"
else
	S_IFOLD="IFOLD=0"
	S_IBEAMFOLD="IBEAMFOLD=0"
	S_IBUNCH="IBUNCH=0"
	S_NBUNCH="NBUNCH=1"
fi
S_PERL="s/IFOLD=[0-9]*/$S_IFOLD/g"
perl -pi -e $S_PERL wavePreScan.in
S_PERL="s/IBEAMFOLD=[0-9]*/$S_IBEAMFOLD/g"
perl -pi -e $S_PERL wavePreScan.in
S_PERL="s/IBUNCH=[0-9]*\s/$S_IBUNCH\t/g"
perl -pi -e $S_PERL wavePreScan.in
S_PERL="s/\s+NBUNCH=[0-9]*/$S_NBUNCH/g"
perl -pi -e $S_PERL wavePreScan.in

# electron emittance folding
N_BSIGZ=2.16E-04
N_BSIGZP=2.48E-05
N_BSIGY=1.87E-05
N_BSIGYP=4.29E-06
S_BSIGZ="BSIGZ\(1\)=$N_BSIGZ"
S_PERL="s/BSIGZ\(1\)=[0-9]*\.[0-9E+-]*/$S_BSIGZ/g"
#perl -pi -e $S_PERL wavePreScan.in
S_BSIGZP="BSIGZP\(1\)=$N_BSIGZP"
S_PERL="s/BSIGZP\(1\)=[0-9]*\.[0-9E+-]*/$S_BSIGZP/g"
#perl -pi -e $S_PERL wavePreScan.in
S_BSIGY="BSIGY\(1\)=$N_BSIGY"
S_PERL="s/BSIGY\(1\)=[0-9]*\.[0-9E+-]*/$S_BSIGY/g"
#perl -pi -e $S_PERL wavePreScan.in
S_BSIGYP="BSIGYP\(1\)=$N_BSIGYP"
S_PERL="s/BSIGYP\(1\)=[0-9]*\.[0-9E+-]*/$S_BSIGYP/g"
#perl -pi -e $S_PERL wavePreScan.in

return

# Schleife über Energie
# for ((EV=80;EV<=570;EV+=10))
for ((EV=80;EV<=570;EV+=10))
do
	cp wavePreScan.in wave.in
#	HARMELL=$(echo "scale=2;($EV+0.5*$EV/100)" | bc -l )
  HARMELL=$EV
#	FREQLOW=$(echo "scale=2;($EV-sqrt($EV/10))" | bc -l )
  FREQLOW=$(echo "scale=2;($EV-($EV/($N_NHARMELL*$N_PERELLIP)*1.8))" | bc -l )
#	FREQHIG=$(echo "scale=2;($EV+sqrt($EV/10))" | bc -l )
  FREQHIG=$(echo "scale=2;($EV+($EV/($N_NHARMELL*$N_PERELLIP)*0.8))" | bc -l )
	IFREQ2P=3
echo $HARMELL
echo $FREQLOW
echo $FREQHIG
echo $IFREQ2P

	S_HARMELL="HARMELL=${HARMELL}"
	S_PERL="s/HARMELL=[0-9]*\.[0-9]*/$S_HARMELL/g"
	perl -pi -e $S_PERL wave.in
	S_FREQLOW="FREQLOW=${FREQLOW}"
	S_PERL="s/FREQLOW=[0-9]*\.[0-9]*/$S_FREQLOW/g"
	perl -pi -e $S_PERL wave.in
	S_FREQHIG="FREQHIG=${FREQHIG}"
	S_PERL="s/FREQHIG=[0-9]*\.[0-9]*/$S_FREQHIG/g"
	perl -pi -e $S_PERL wave.in
	S_IFREQ2P="IFREQ2P=${IFREQ2P}"
	S_PERL="s/IFREQ2P=[0-9]*/$S_IFREQ2P/g"
	perl -pi -e $S_PERL wave.in

# scale down pinhole rastersteps for integration (for getting flux optimized value)
	S_MPINZ="MPINZ=71"
	S_PERL="s/MPINZ=[0-9]*/$S_MPINZ/g"
	perl -pi -e $S_PERL wave.in
	S_MPINY="MPINY=71"
	S_PERL="s/MPINY=[0-9]*/$S_MPINY/g"
	perl -pi -e $S_PERL wave.in

# Start wave for each energy

# Create Result Folder:
	FNAME="${EV}eV"
	mkdir -p "${ONAME}"
        cp wave.in "${ONAME}/."
	cd $ONAME

	if [ "$1" == "wave" ]
	then
	echo "run 'int'-mode to get maximum energy!"
	$WAVE/stage/wave

	mkdir -p "${FNAME}"
  mkdir -p "${RAYFILES}"
	cp wave.in "${FNAME}/wave_${ONAME}_${EV}eV_int.in"
  cp wave.out "${FNAME}/wave_${ONAME}_${EV}eV_int.out"
  cp wave_ray.dat "${FNAME}/${ONAME}_${EV}_int.dat"
	#cp wave_ray.dat "${RAYFILES}/${ONAME}_${EV}_int.dat"

	rm wave_ray.dat

	else
		echo "test 'int'-mode run, no  Simulation"
	fi

	RESULT_LINE_FLUX=$(grep -A2 'Estimated maximum:' wave.out | grep -B1 '\-\-' | head -n1)
        A_FLUX=( $RESULT_LINE_FLUX )

	RESULT_LINE_FLUXE=$(grep -A2 'Estimated maximum:' wave.out| grep -m2 -A3 '\-\-' | tail -n1)
        A_FLUXE=( $RESULT_LINE_FLUXE )

	RESULT_LINE_POWER=$(grep -A2 'Power through pinhole' wave.out | tail -n1)
	A_POWER=( $RESULT_LINE_POWER )

#	RESULT_LINE_FLUX_BO=$(head -n1 brill_flux.dat)
#	A_FLUX_BO=( $RESULT_LINE_FLUX_BO )

# scale up pinhole rastersteps for all other
	S_MPINZ="MPINZ=151"
	S_PERL="s/MPINZ=[0-9]*/$S_MPINZ/g"
	perl -pi -e $S_PERL wave.in
	S_MPINY="MPINY=151"
	S_PERL="s/MPINY=[0-9]*/$S_MPINY/g"
	perl -pi -e $S_PERL wave.in

# FO run at max energy:

 if [ "${A_FLUX[0]}" == "" ]
 then FREQLOW="0.0"
 else
  FREQLOW=${A_FLUX[0]}
 fi
	IFREQ2P=1
echo "FO flux: "$FREQLOW
echo $IFREQ2P
	S_FREQLOW="FREQLOW=${FREQLOW}"
	S_PERL="s/FREQLOW=[0-9]*\.[0-9]*/$S_FREQLOW/g"
	perl -pi -e $S_PERL wave.in
	S_IFREQ2P="IFREQ2P=${IFREQ2P}"
	S_PERL="s/IFREQ2P=[0-9]*/$S_IFREQ2P/g"
	perl -pi -e $S_PERL wave.in

if [ "$1" == "wave" ]
then
echo "'FO': run at maximum energy"
$WAVE/stage/wave

mkdir -p "${FNAME}"
mkdir -p "${RAYFILES}"
cp wave.in "${FNAME}/wave_${ONAME}_${EV}eV_fo.in"
cp wave.out "${FNAME}/wave_${ONAME}_${EV}eV_fo.out"
cp wave_ray.dat "${FNAME}/${ONAME}_${EV}_fo.dat"
cp wave_ray.dat "${RAYFILES}/${ONAME}_${EV}_fo.dat"

rm wave_ray.dat

else
  echo "test 'FO'-run, no  Simulation"
fi

# run wave at figure of merit flux/rms (???):
#	FREQLOW=$(echo "scale=2;($EV-sqrt($EV/10))" | bc -l )

  FREQLOW=$(echo "scale=2;($EV-($EV/($N_NHARMELL*$N_PERELLIP))*0.5)" | bc -l )
	IFREQ2P=1
echo "FM energy: " $FREQLOW
echo $IFREQ2P
	S_FREQLOW="FREQLOW=${FREQLOW}"
	S_PERL="s/FREQLOW=[0-9]*\.[0-9]*/$S_FREQLOW/g"
	perl -pi -e $S_PERL wave.in
	S_IFREQ2P="IFREQ2P=${IFREQ2P}"
	S_PERL="s/IFREQ2P=[0-9]*/$S_IFREQ2P/g"
	perl -pi -e $S_PERL wave.in

if [ "$1" == "wave" ]
then
echo "'FM'-run at figure of merit = 0.47*E/n/N"
$WAVE/stage/wave

mkdir -p "${FNAME}"
mkdir -p "${RAYFILES}"
cp wave.in "${FNAME}/wave_${ONAME}_${EV}eV_fm.in"
cp wave.out "${FNAME}/wave_${ONAME}_${EV}eV_fm.out"
cp wave_ray.dat "${FNAME}/${ONAME}_${EV}_fm.dat"
cp wave_ray.dat "${RAYFILES}/${ONAME}_${EV}_fm.dat"

rm wave_ray.dat

RESULT_LINE_FLUX_FM=$(grep -A3 'Photon energy or wavelength and flux through pinhole' wave.out | tail -n1)
A_FLUX_FM=( $RESULT_LINE_FLUX_FM )

else
	echo "test 'FM'-run, no  Simulation"
fi

# run wave at best brilliance at $EV for getting wave_ray.dat file :
#	FREQLOW=$(echo "scale=2;($EV-sqrt($EV/10))" | bc -l )
  FREQLOW=$(echo "scale=2;($EV-($EV/($N_NHARMELL*$N_PERELLIP))*0.0)" | bc -l )
	IFREQ2P=1
echo "BO energy: "$FREQLOW
echo $IFREQ2P
	S_FREQLOW="FREQLOW=${FREQLOW}"
	S_PERL="s/FREQLOW=[0-9]*\.[0-9]*/$S_FREQLOW/g"
	perl -pi -e $S_PERL wave.in
	S_IFREQ2P="IFREQ2P=${IFREQ2P}"
	S_PERL="s/IFREQ2P=[0-9]*/$S_IFREQ2P/g"
	perl -pi -e $S_PERL wave.in

if [ "$1" == "wave" ]
then
echo "'BO'-run: at best brilliance = run at $EV"
$WAVE/stage/wave

mkdir -p "${FNAME}"
mkdir -p "${RAYFILES}"
cp wave.in "${FNAME}/wave_${ONAME}_${EV}eV_bo.in"
cp wave.out "${FNAME}/wave_${ONAME}_${EV}eV_bo.out"
cp wave_ray.dat "${FNAME}/${ONAME}_${EV}_bo.dat"
cp wave_ray.dat "${RAYFILES}/${ONAME}_${EV}_bo.dat"

rm wave_ray.dat

RESULT_LINE_FLUX_BO=$(grep -A3 'Photon energy or wavelength and flux through pinhole' wave.out | tail -n1)
A_FLUX_BO=( $RESULT_LINE_FLUX_BO )

else
	echo "test 'BO'-run, no  Simulation"
fi

# HEADER_RFILE="set_energy	fo_energy	fo_flux	fm_energy	fm_flux	bo_flux	max_energy_emittance	flux_emittance	power_all	power_sum"

echo "${EV}	${A_FLUX[0]}	${A_FLUX[1]}	${A_FLUX_FM[0]}	${A_FLUX_FM[1]}	${A_FLUX_BO[0]}	${A_FLUX_BO[1]}	${A_FLUXE[0]}	${A_FLUXE[1]}	${A_POWER[0]}	${A_POWER[1]}" | tee -a $RFILE

cd $SCRIPTPATH
done

cp "${RFILE}" "${ONAME}/${ONAME}_RESULTS.dat"
cp "runWAVE.sh" "${ONAME}/${ONAME}_runWAVE.sh"
rm "${ONAME}/WAVE.mhb"
rm "${ONAME}/WAVE.root"
rm "${ONAME}/WAVE.root.bck"
rm ${ONAME}/*.scr
rm ${ONAME}/brill_*.dat
