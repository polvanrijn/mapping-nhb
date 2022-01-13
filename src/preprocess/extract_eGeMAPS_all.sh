module load conda
source activate production_MAPS
export PATH=${PATH}:$HOME/software/opensmile/bin/

for value in AHOEMO1 AHOEMO2 CaFE CREMA-D DaFEX DB_Arabic EEKK EMA EMO-DB EmoHI EmoV-DB eNTERFACE ESCAD GEMEP IITKGP_SEHSC IITKGP_SESC JUSLIN_LAUKKA_2001 MAP_HAWK MSP_improv PAX RAVDESS SAVEE TESS VENEC
do
    echo $value
    python extract_openSMLIE.py -i /scratch/pvanrij/corpora/${value}/preprocessed -o ../../data/${value}_eGeMAPS.csv
done
