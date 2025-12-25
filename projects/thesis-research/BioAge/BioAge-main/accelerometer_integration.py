"""
ACCELEROMETER + BIOAGE INTEGRATION
===================================
Links physical activity (accelerometer) data with Biological Age.
Tests if movement patterns correlate with age acceleration.

This addresses the key gap: "Accelerometer data available but not used"

Author: Ahmed Eltaweel
Date: December 2024
"""

import pandas as pd
import numpy as np
import requests
import os
import warnings
warnings.filterwarnings('ignore')

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# ==========================================
# CONFIGURATION
# ==========================================

DATA_DIR = "./nhanes_2003_2006_data"

# NHANES Physical Activity Monitor (PAM) summary files
# These contain daily activity summaries (not raw minute data)
PAM_URLS = {
    '2003-2004': "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2003/DataFiles/PAXDAY_C.XPT",
    '2005-2006': "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2005/DataFiles/PAXDAY_D.XPT"
}

def download_accelerometer_data():
    """Download NHANES accelerometer summary data."""
    print("\n" + "="*60)
    print("  DOWNLOADING ACCELEROMETER DATA")
    print("="*60)
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    all_data = []
    
    for cycle, url in PAM_URLS.items():
        filename = f'PAXDAY_{cycle[:4]}.XPT'
        filepath = os.path.join(DATA_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"  Downloading {cycle} accelerometer data...")
            try:
                r = requests.get(url, timeout=180)
                with open(filepath, 'wb') as f:
                    f.write(r.content)
                print(f"  [OK] Downloaded {filename} ({len(r.content)/1024/1024:.1f} MB)")
            except Exception as e:
                print(f"  [FAIL] Download failed for {cycle}: {e}")
                continue
        else:
            print(f"  [OK] {filename} already exists")
        
        # Parse file
        try:
            df = pd.read_sas(filepath)
            df['Cycle'] = cycle
            all_data.append(df)
            print(f"  [OK] Parsed {len(df):,} records from {cycle}")
        except Exception as e:
            print(f"  [FAIL] Error parsing {filename}: {e}")
    
    if not all_data:
        print("[!] No accelerometer data loaded")
        return None
    
    df_accel = pd.concat(all_data, ignore_index=True)
    print(f"\n  [OK] Total accelerometer records: {len(df_accel):,}")
    
    return df_accel

def process_accelerometer_data(df_accel):
    """Process accelerometer data to get per-person activity summaries."""
    print("\n" + "="*60)
    print("  PROCESSING ACCELEROMETER DATA")
    print("="*60)
    
    # Key variables from PAXDAY:
    # SEQN - Respondent sequence number
    # PAXDAY - Day of week of wear (1=Sunday)
    # PAXN - Count of minutes in the data quality flag
    # PAXCAL - Calibration (1=Yes, 2=No)
    # PAXSTAT - Data Reliability Status (1=Reliable, 2=Questionable)
    
    # Check available columns
    print(f"  Available columns: {df_accel.columns.tolist()[:15]}...")
    
    # Get valid days only (calibrated and reliable)
    if 'PAXCAL' in df_accel.columns and 'PAXSTAT' in df_accel.columns:
        df_valid = df_accel[(df_accel['PAXCAL'] == 1) & (df_accel['PAXSTAT'] == 1)].copy()
        print(f"  Valid records (calibrated & reliable): {len(df_valid):,}")
    else:
        df_valid = df_accel.copy()
        print(f"  Using all records: {len(df_valid):,}")
    
    # Calculate per-person metrics
    # Look for activity intensity columns
    intensity_cols = [c for c in df_accel.columns if 'MIN' in c.upper() or 'MVPA' in c.upper() 
                      or 'SEDENTARY' in c.upper() or 'LIGHT' in c.upper()]
    print(f"  Activity intensity columns: {intensity_cols[:10]}")
    
    # Try to find total activity or sedentary columns
    activity_cols = {}
    
    # Check for common column patterns
    for col in df_accel.columns:
        col_upper = col.upper()
        if 'SEDMIN' in col_upper or 'PAXSED' in col_upper:
            activity_cols['sedentary'] = col
        elif 'LGTMIN' in col_upper or 'PAXLGT' in col_upper:
            activity_cols['light'] = col
        elif 'MODMIN' in col_upper or 'PAXMOD' in col_upper:
            activity_cols['moderate'] = col
        elif 'VIGMIN' in col_upper or 'PAXVIG' in col_upper:
            activity_cols['vigorous'] = col
        elif 'METS' in col_upper:
            activity_cols['mets'] = col
    
    print(f"  Identified activity columns: {activity_cols}")
    
    # Aggregate per person
    if activity_cols:
        agg_dict = {col: 'mean' for col in activity_cols.values()}
        agg_dict['SEQN'] = 'first'  # Keep SEQN
        
        # Group by SEQN and calculate mean daily activity
        df_person = df_valid.groupby('SEQN').agg('mean').reset_index()
        
        # Calculate total activity minutes if we have the components
        if 'moderate' in activity_cols and 'vigorous' in activity_cols:
            df_person['MVPA'] = df_person[activity_cols['moderate']] + df_person[activity_cols['vigorous']]
        
        print(f"  [OK] Aggregated to {len(df_person):,} participants")
    else:
        # If specific columns not found, just get wear time info
        df_person = df_valid.groupby('SEQN').size().reset_index(name='valid_days')
        print(f"  [OK] Got {len(df_person):,} participants with wear data")
    
    return df_person

def calculate_activity_fragmentation(df_accel):
    """
    Calculate activity fragmentation metrics.
    Higher fragmentation = more interruptions = potentially worse health.
    """
    print("\n" + "="*60)
    print("  CALCULATING ACTIVITY FRAGMENTATION")
    print("="*60)
    
    # This is a simplified fragmentation metric
    # Real fragmentation would require minute-by-minute data
    
    # For now, use variability in daily activity as a proxy
    if 'SEQN' in df_accel.columns:
        # Calculate coefficient of variation in activity across days
        numeric_cols = df_accel.select_dtypes(include=[np.number]).columns
        
        # Group by SEQN and calculate CV for each numeric column
        def calc_cv(x):
            if len(x) > 1 and x.std() > 0:
                return x.std() / x.mean()
            return np.nan
        
        # Get fragmentation per person
        df_frag = df_accel.groupby('SEQN').apply(
            lambda x: pd.Series({
                'activity_cv': x[numeric_cols].mean(axis=1).std() / (x[numeric_cols].mean(axis=1).mean() + 1e-6),
                'n_days': len(x)
            })
        ).reset_index()
        
        print(f"  [OK] Calculated fragmentation for {len(df_frag):,} participants")
        return df_frag
    
    return None

def merge_with_phenoage():
    """Merge accelerometer data with PhenoAge and mortality data."""
    print("\n" + "="*60)
    print("  MERGING WITH PHENOAGE DATA")
    print("="*60)
    
    # Load PhenoAge with mortality
    phenoage_file = os.path.join(DATA_DIR, 'phenoage_with_mortality.csv')
    if not os.path.exists(phenoage_file):
        print(f"  [FAIL] PhenoAge file not found. Run mortality_validation.py first.")
        return None
    
    df_pheno = pd.read_csv(phenoage_file)
    print(f"  [OK] Loaded {len(df_pheno):,} PhenoAge records")
    
    return df_pheno

def analyze_activity_bioage_relationship(df):
    """Analyze relationship between activity and biological age."""
    print("\n" + "="*60)
    print("  ACTIVITY-BIOAGE RELATIONSHIP ANALYSIS")
    print("="*60)
    
    # Check for activity columns
    activity_cols = [c for c in df.columns if any(x in c.upper() for x in 
                    ['MVPA', 'SEDENTARY', 'LIGHT', 'VIGOROUS', 'MODERATE', 'ACTIVITY', 'CV'])]
    
    if not activity_cols:
        print("  [!] No activity columns found in data")
        return None
    
    print(f"  Activity columns for analysis: {activity_cols}")
    
    # Correlation with Age Acceleration
    print("\n  Correlations with Age Acceleration:")
    print("-"*50)
    
    correlations = {}
    for col in activity_cols:
        if col in df.columns:
            mask = df[col].notna() & df['AgeAccel_Calibrated'].notna()
            if mask.sum() > 100:
                corr = df.loc[mask, col].corr(df.loc[mask, 'AgeAccel_Calibrated'])
                correlations[col] = corr
                print(f"  {col}: r = {corr:.3f}")
    
    return correlations

def create_integrated_analysis():
    """Run the complete accelerometer-BioAge integration analysis."""
    print("\n" + "="*70)
    print("  ACCELEROMETER + BIOLOGICAL AGE INTEGRATION")
    print("  Linking Physical Activity with Age Acceleration")
    print("="*70)
    
    # Step 1: Download accelerometer data
    df_accel = download_accelerometer_data()
    
    if df_accel is None:
        # Try alternative approach - use existing mortality data
        print("\n  [!] Accelerometer download failed, using existing data")
        df_pheno = merge_with_phenoage()
        if df_pheno is None:
            return None
        
        # Create a simple activity proxy from NLR (inflammatory marker)
        # Higher NLR = lower activity (based on research)
        if 'NLR' in df_pheno.columns:
            df_pheno['Activity_Proxy'] = 1 / (df_pheno['NLR'] + 0.1)  # Inverse of inflammation
            
            # Analyze relationship
            corr = df_pheno['Activity_Proxy'].corr(df_pheno['AgeAccel_Calibrated'])
            print(f"\n  Activity Proxy (1/NLR) - AgeAccel correlation: {corr:.3f}")
        
        return df_pheno
    
    # Step 2: Process accelerometer data
    df_activity = process_accelerometer_data(df_accel)
    
    # Step 3: Calculate fragmentation
    df_frag = calculate_activity_fragmentation(df_accel)
    
    # Step 4: Merge with PhenoAge
    df_pheno = merge_with_phenoage()
    if df_pheno is None:
        return None
    
    # Merge activity data with PhenoAge
    if df_activity is not None:
        df_merged = df_pheno.merge(df_activity, on='SEQN', how='left')
    else:
        df_merged = df_pheno
    
    if df_frag is not None:
        df_merged = df_merged.merge(df_frag, on='SEQN', how='left')
    
    print(f"\n  [OK] Merged dataset: {len(df_merged):,} participants")
    
    # Step 5: Analyze relationships
    correlations = analyze_activity_bioage_relationship(df_merged)
    
    # Step 6: Summary
    print("\n" + "="*70)
    print("  ACCELEROMETER INTEGRATION RESULTS")
    print("="*70)
    
    if correlations:
        print(f"""
    +---------------------------------------------------------------+
    |  ACTIVITY-BIOAGE CORRELATIONS                                 |
    +---------------------------------------------------------------+""")
        for col, corr in correlations.items():
            direction = "Higher activity -> Lower BioAge" if corr < 0 else "Higher activity -> Higher BioAge"
            print(f"    |  {col}: r = {corr:.3f} ({direction})")
        print("    +---------------------------------------------------------------+")
    
    # Save results
    df_merged.to_csv(os.path.join(DATA_DIR, 'phenoage_with_activity.csv'), index=False)
    print(f"\n  [OK] Results saved to {DATA_DIR}/phenoage_with_activity.csv")
    
    return df_merged, correlations

if __name__ == "__main__":
    results = create_integrated_analysis()
