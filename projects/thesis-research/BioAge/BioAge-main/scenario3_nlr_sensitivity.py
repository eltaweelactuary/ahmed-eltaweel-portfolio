"""
Scenario 3: NLR-Based Sensitivity Analysis
===========================================
Uses Neutrophil-to-Lymphocyte Ratio as inflammation proxy instead of CRP.
Validates that the model is robust to different inflammatory markers.

Author: Ahmed Eltaweel
Date: December 2024
"""

import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = "./nhanes_2003_2006_data"

def run_nlr_sensitivity():
    """Run NLR sensitivity analysis on NHANES 2003-2006 data."""
    print("\n" + "="*70)
    print("  SCENARIO 3: NLR SENSITIVITY ANALYSIS")
    print("  Testing inflammation proxy alternatives to CRP")
    print("="*70)
    
    # Load existing NHANES 2003-2006 results
    csv_path = os.path.join(DATA_DIR, 'nhanes_2003_2006_phenoage_results.csv')
    if not os.path.exists(csv_path):
        print("[!] NHANES 2003-2006 results not found. Run nhanes_2003_2006_validation.py first.")
        return None
    
    df = pd.read_csv(csv_path)
    print(f"\n  Loaded {len(df):,} participants from NHANES 2003-2006")
    
    # Calculate NLR (Neutrophil-to-Lymphocyte Ratio)
    # Neutrophils = Total WBC - (Lymphocytes + other cells)
    # Approximate: Neutrophils ~ WBC * (100 - Lymphocyte%) / 100
    df['Neutrophil_Est'] = df['WBC'] * (100 - df['Lymphocyte_Pct']) / 100
    df['Lymphocyte_Count'] = df['WBC'] * df['Lymphocyte_Pct'] / 100
    df['NLR'] = df['Neutrophil_Est'] / df['Lymphocyte_Count']
    
    # Remove extreme NLR values
    df = df[(df['NLR'] > 0.5) & (df['NLR'] < 20)].copy()
    print(f"  After NLR filter (0.5-20): {len(df):,} participants")
    
    # Analysis 1: Correlation Matrix
    print("\n" + "-"*50)
    print("  CORRELATION ANALYSIS")
    print("-"*50)
    
    corr_matrix = df[['CRP', 'NLR', 'AgeAccel_Calibrated', 'Age', 'log_CRP']].corr()
    print("\n  Correlation Matrix:")
    print(corr_matrix.round(3).to_string())
    
    # Key correlations
    nlr_crp = corr_matrix.loc['NLR', 'CRP']
    nlr_accel = corr_matrix.loc['NLR', 'AgeAccel_Calibrated']
    crp_accel = corr_matrix.loc['CRP', 'AgeAccel_Calibrated']
    
    print(f"\n  Key Findings:")
    print(f"  - NLR-CRP Correlation:         {nlr_crp:.3f}")
    print(f"  - NLR-AgeAccel Correlation:    {nlr_accel:.3f}")
    print(f"  - CRP-AgeAccel Correlation:    {crp_accel:.3f}")
    
    # Analysis 2: NLR Quintiles vs Age Acceleration
    print("\n" + "-"*50)
    print("  NLR QUINTILE ANALYSIS")
    print("-"*50)
    
    df['NLR_Quintile'] = pd.qcut(df['NLR'], q=5, labels=['Q1_Low', 'Q2', 'Q3', 'Q4', 'Q5_High'])
    
    nlr_stats = df.groupby('NLR_Quintile').agg({
        'NLR': ['mean', 'count'],
        'AgeAccel_Calibrated': 'mean',
        'CRP': 'mean'
    }).round(3)
    
    print("\n  NLR Quintile Statistics:")
    print(nlr_stats.to_string())
    
    # Analysis 3: Regression Comparison
    print("\n" + "-"*50)
    print("  PREDICTIVE POWER COMPARISON")
    print("-"*50)
    
    # Simple linear regression R-squared
    from numpy.polynomial import polynomial as P
    
    # CRP predicting Age Acceleration
    mask_crp = ~(np.isnan(df['log_CRP']) | np.isnan(df['AgeAccel_Calibrated']))
    if mask_crp.sum() > 0:
        x_crp = df.loc[mask_crp, 'log_CRP'].values
        y = df.loc[mask_crp, 'AgeAccel_Calibrated'].values
        corr_crp = np.corrcoef(x_crp, y)[0,1]
        r2_crp = corr_crp ** 2
    else:
        r2_crp = 0
    
    # NLR predicting Age Acceleration
    mask_nlr = ~(np.isnan(df['NLR']) | np.isnan(df['AgeAccel_Calibrated']))
    if mask_nlr.sum() > 0:
        x_nlr = df.loc[mask_nlr, 'NLR'].values
        y = df.loc[mask_nlr, 'AgeAccel_Calibrated'].values
        corr_nlr = np.corrcoef(x_nlr, y)[0,1]
        r2_nlr = corr_nlr ** 2
    else:
        r2_nlr = 0
    
    print(f"  R-squared (log_CRP -> AgeAccel): {r2_crp:.4f}")
    print(f"  R-squared (NLR -> AgeAccel):     {r2_nlr:.4f}")
    print(f"  NLR captures {100*r2_nlr/r2_crp:.1f}% of CRP's predictive power" if r2_crp > 0 else "")
    
    # Analysis 4: Combined Model
    print("\n" + "-"*50)
    print("  GINI COEFFICIENT COMPARISON")
    print("-"*50)
    
    # Calculate Gini for CRP-based quintiles
    values = df['AgeAccel_Calibrated'].values
    shifted = values - values.min() + 1
    sorted_vals = np.sort(shifted)
    n = len(sorted_vals)
    index = np.arange(1, n + 1)
    gini_crp = (2 * np.sum(index * sorted_vals) - (n + 1) * np.sum(sorted_vals)) / (n * np.sum(sorted_vals))
    
    # Calculate Gini based on NLR quintiles
    df_nlr = df.copy()
    df_nlr['AgeAccel_NLR'] = df_nlr.groupby('NLR_Quintile')['AgeAccel_Calibrated'].transform('mean')
    values_nlr = df_nlr['AgeAccel_NLR'].values
    shifted_nlr = values_nlr - values_nlr.min() + 1
    sorted_nlr = np.sort(shifted_nlr)
    gini_nlr = (2 * np.sum(index * sorted_nlr) - (n + 1) * np.sum(sorted_nlr)) / (n * np.sum(sorted_nlr))
    
    print(f"  Gini (CRP-based PhenoAge):  {gini_crp:.3f}")
    print(f"  Gini (NLR-stratified):      {gini_nlr:.3f}")
    
    # Final Summary
    print("\n" + "="*70)
    print("  SCENARIO 3 RESULTS - NLR SENSITIVITY")
    print("="*70)
    print(f"""
    +-------------------------------------------------------------+
    |  Dataset:                        NHANES 2003-2006           |
    |  Sample Size:                    {len(df):,} participants        |
    |  NLR-CRP Correlation:            {nlr_crp:.3f}                       |
    |  NLR-AgeAccel Correlation:       {nlr_accel:.3f}                       |
    |  NLR Predictive Power (R2):      {r2_nlr:.4f}                     |
    |  CRP Predictive Power (R2):      {r2_crp:.4f}                     |
    |  NLR vs CRP Power Ratio:         {100*r2_nlr/r2_crp:.1f}%                       |
    +-------------------------------------------------------------+
    
    CONCLUSION: NLR can serve as a PARTIAL proxy for CRP ({100*r2_nlr/r2_crp:.1f}% power).
    Recommended for sensitivity analysis, NOT as primary replacement.
    """)
    
    # Save results
    df.to_csv(os.path.join(DATA_DIR, 'scenario3_nlr_sensitivity.csv'), index=False)
    print(f"[OK] Results saved to {DATA_DIR}/scenario3_nlr_sensitivity.csv")
    
    return {
        'nlr_crp_corr': nlr_crp,
        'nlr_accel_corr': nlr_accel,
        'r2_nlr': r2_nlr,
        'r2_crp': r2_crp,
        'power_ratio': r2_nlr/r2_crp if r2_crp > 0 else 0
    }

if __name__ == "__main__":
    results = run_nlr_sensitivity()
