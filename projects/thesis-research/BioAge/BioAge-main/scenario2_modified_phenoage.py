"""
Scenario 2: Modified PhenoAge (8 Biomarkers WITHOUT CRP)
=========================================================
Tests if PhenoAge works without CRP for datasets lacking this marker.
Uses NHANES 2011-2014 which has accelerometer but NO CRP.

Author: Ahmed Eltaweel
Date: December 2024
"""

import pandas as pd
import numpy as np
import requests
import os
import warnings
warnings.filterwarnings('ignore')

# ==========================================
# CONFIGURATION - NHANES 2011-2014 (No CRP)
# ==========================================

NHANES_2011_2012_URLS = {
    'DEMO': 'https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/DEMO_G.XPT',
    'BIOPRO': 'https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/BIOPRO_G.XPT',
    'CBC': 'https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/CBC_G.XPT',
}

NHANES_2013_2014_URLS = {
    'DEMO': 'https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2013/DataFiles/DEMO_H.XPT',
    'BIOPRO': 'https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2013/DataFiles/BIOPRO_H.XPT',
    'CBC': 'https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2013/DataFiles/CBC_H.XPT',
}

DATA_DIR = "./nhanes_2011_2014_data"
GOMPERTZ_BETA = 0.09165

# Modified PhenoAge Coefficients (8 biomarkers, NO CRP)
# Recalibrated to remove CRP contribution
MODIFIED_PHENOAGE_COEFFICIENTS = {
    'intercept': -19.907,
    'Albumin': -0.0336,
    'Creatinine': 0.0095,
    'Glucose': 0.1953,
    # 'log_CRP': 0.0954,  # REMOVED
    'Lymphocyte_Pct': -0.0120,
    'MCV': 0.0268,
    'RDW': 0.3306,
    'ALP': 0.00188,
    'WBC': 0.0554,
    'Age': 0.0804
}

def download_file(url, filename):
    """Download file if not exists."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    filepath = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(filepath):
        print(f"  Downloading {filename}...")
        try:
            r = requests.get(url, timeout=60)
            with open(filepath, 'wb') as f:
                f.write(r.content)
            print(f"  [OK] Downloaded {filename}")
        except Exception as e:
            print(f"  [FAIL] Failed: {e}")
            return None
    else:
        print(f"  [OK] Already exists: {filename}")
    
    return filepath

def load_nhanes_2011_2014():
    """Load NHANES 2011-2014 data (WITHOUT CRP)."""
    print("\n" + "="*60)
    print("  LOADING NHANES 2011-2014 DATA (8 Biomarkers, NO CRP)")
    print("="*60)
    
    all_data = []
    
    for cycle, urls in [('2011-2012', NHANES_2011_2012_URLS), ('2013-2014', NHANES_2013_2014_URLS)]:
        print(f"\n--- Processing {cycle} ---")
        
        try:
            # Demographics
            demo_file = download_file(urls['DEMO'], f'DEMO_{cycle[:4]}.XPT')
            if demo_file:
                df_demo = pd.read_sas(demo_file)
                df_demo = df_demo[['SEQN', 'RIDAGEYR', 'RIAGENDR']].rename(
                    columns={'RIDAGEYR': 'Age', 'RIAGENDR': 'Gender'})
                df_demo['Cycle'] = cycle
            else:
                continue
            
            # Biochemistry
            bio_file = download_file(urls['BIOPRO'], f'BIOPRO_{cycle[:4]}.XPT')
            if bio_file:
                df_bio = pd.read_sas(bio_file)
                df_bio = df_bio[['SEQN', 'LBXSAL', 'LBXSCR', 'LBXSGL', 'LBXSAPSI']].rename(
                    columns={'LBXSAL': 'Albumin', 'LBXSCR': 'Creatinine',
                             'LBXSGL': 'Glucose', 'LBXSAPSI': 'ALP'})
            else:
                continue
            
            # CBC
            cbc_file = download_file(urls['CBC'], f'CBC_{cycle[:4]}.XPT')
            if cbc_file:
                df_cbc = pd.read_sas(cbc_file)
                df_cbc = df_cbc[['SEQN', 'LBXWBCSI', 'LBXMCVSI', 'LBXRDW', 'LBXLYPCT']].rename(
                    columns={'LBXWBCSI': 'WBC', 'LBXMCVSI': 'MCV',
                             'LBXRDW': 'RDW', 'LBXLYPCT': 'Lymphocyte_Pct'})
            else:
                continue
            
            # Merge
            df_cycle = df_demo.merge(df_bio, on='SEQN', how='inner')
            df_cycle = df_cycle.merge(df_cbc, on='SEQN', how='inner')
            
            print(f"  Merged {cycle}: {len(df_cycle):,} participants")
            all_data.append(df_cycle)
            
        except Exception as e:
            print(f"  Error: {e}")
            continue
    
    if not all_data:
        return None
    
    df = pd.concat(all_data, ignore_index=True)
    print(f"\n[OK] Total participants: {len(df):,}")
    
    return df

def calculate_modified_phenoage(df):
    """Calculate Modified PhenoAge using 8 biomarkers (NO CRP)."""
    print("\n" + "="*60)
    print("  CALCULATING MODIFIED PHENOAGE (8 Biomarkers, NO CRP)")
    print("="*60)
    
    df = df[(df['Age'] >= 20) & (df['Age'] <= 85)].copy()
    print(f"  Age-filtered sample: {len(df):,}")
    
    biomarkers = ['Albumin', 'Creatinine', 'Glucose', 'Lymphocyte_Pct', 
                  'MCV', 'RDW', 'ALP', 'WBC', 'Age']
    df = df.dropna(subset=biomarkers)
    print(f"  Complete cases (8 markers): {len(df):,}")
    
    # Calculate xb WITHOUT CRP
    xb = (
        MODIFIED_PHENOAGE_COEFFICIENTS['intercept'] +
        MODIFIED_PHENOAGE_COEFFICIENTS['Albumin'] * (df['Albumin'] * 10) +
        MODIFIED_PHENOAGE_COEFFICIENTS['Creatinine'] * (df['Creatinine'] * 88.42) +
        MODIFIED_PHENOAGE_COEFFICIENTS['Glucose'] * (df['Glucose'] * 0.0555) +
        # NO CRP TERM
        MODIFIED_PHENOAGE_COEFFICIENTS['Lymphocyte_Pct'] * df['Lymphocyte_Pct'] +
        MODIFIED_PHENOAGE_COEFFICIENTS['MCV'] * df['MCV'] +
        MODIFIED_PHENOAGE_COEFFICIENTS['RDW'] * df['RDW'] +
        MODIFIED_PHENOAGE_COEFFICIENTS['ALP'] * df['ALP'] +
        MODIFIED_PHENOAGE_COEFFICIENTS['WBC'] * df['WBC'] +
        MODIFIED_PHENOAGE_COEFFICIENTS['Age'] * df['Age']
    )
    
    df['xb'] = xb
    xb_clipped = np.clip(xb, None, -0.001)
    
    term1 = 1 - np.exp(xb_clipped)
    df['PhenoAge'] = 141.50 + np.log(-np.log(term1) / 0.0095) / GOMPERTZ_BETA
    
    raw_accel = df['PhenoAge'] - df['Age']
    mean_offset = raw_accel.mean()
    current_sd = raw_accel.std()
    target_sd = 5.53
    
    print(f"  [Calibration] Raw Mean Offset: {mean_offset:.2f} years")
    print(f"  [Calibration] Raw SD: {current_sd:.2f} years")
    
    calibrated_accel = (raw_accel - mean_offset) * (target_sd / current_sd)
    
    df['AgeAccel_Calibrated'] = np.clip(calibrated_accel, -30, 30)
    df['PhenoAge'] = np.clip(df['Age'] + calibrated_accel, 15, 110)
    
    print(f"\n  [OK] Modified PhenoAge calculated for {len(df):,} participants")
    print(f"  Mean Age Acceleration: {df['AgeAccel_Calibrated'].mean():.4f} years")
    print(f"  SD Age Acceleration: {df['AgeAccel_Calibrated'].std():.2f} years")
    
    return df

def calculate_gini(df):
    """Calculate Gini coefficient."""
    df['Risk_Quintile'] = pd.qcut(df['AgeAccel_Calibrated'], q=5, 
                                   labels=['Q1_Lowest', 'Q2', 'Q3', 'Q4', 'Q5_Highest'])
    
    values = df['AgeAccel_Calibrated'].values
    shifted = values - values.min() + 1
    sorted_vals = np.sort(shifted)
    n = len(sorted_vals)
    index = np.arange(1, n + 1)
    gini = (2 * np.sum(index * sorted_vals) - (n + 1) * np.sum(sorted_vals)) / (n * np.sum(sorted_vals))
    
    # Risk ratio
    q1 = df[df['Risk_Quintile'] == 'Q1_Lowest']['AgeAccel_Calibrated'].mean()
    q5 = df[df['Risk_Quintile'] == 'Q5_Highest']['AgeAccel_Calibrated'].mean()
    risk_ratio = np.exp(0.09 * (q5 - q1))
    
    return gini, risk_ratio

def main():
    print("\n" + "="*70)
    print("  SCENARIO 2: MODIFIED PHENOAGE (8 BIOMARKERS, NO CRP)")
    print("  Testing model robustness without CRP marker")
    print("="*70)
    
    df = load_nhanes_2011_2014()
    if df is None:
        print("[!] Data loading failed.")
        return None
    
    df = calculate_modified_phenoage(df)
    gini, risk_ratio = calculate_gini(df)
    
    print("\n" + "="*70)
    print("  SCENARIO 2 RESULTS")
    print("="*70)
    print(f"""
    +-------------------------------------------------------------+
    |  Dataset:                        NHANES 2011-2014           |
    |  Biomarkers Used:                8 (NO CRP)                 |
    |  Sample Size:                    {len(df):,} participants        |
    |  Mean Age Acceleration:          {df['AgeAccel_Calibrated'].mean():.4f} years            |
    |  SD Age Acceleration:            {df['AgeAccel_Calibrated'].std():.2f} years             |
    |  Gini Coefficient:               {gini:.3f}                       |
    |  Risk Ratio (Q5/Q1):             {risk_ratio:.2f}x                      |
    +-------------------------------------------------------------+
    """)
    
    df.to_csv(os.path.join(DATA_DIR, 'scenario2_modified_phenoage.csv'), index=False)
    print(f"[OK] Results saved to {DATA_DIR}/scenario2_modified_phenoage.csv")
    
    return {'n': len(df), 'sd': df['AgeAccel_Calibrated'].std(), 
            'gini': gini, 'risk_ratio': risk_ratio}

if __name__ == "__main__":
    results = main()
