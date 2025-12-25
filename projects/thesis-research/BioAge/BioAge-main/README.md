
# BioAge Pricing Framework - Code Repository

This repository contains the source code for the Master's Thesis: "**Optimizing Actuarial Pricing Using Biological Age**".

## 🚀 Execution Order (Validation Pipeline)

To replicate the thesis results, run the scripts in the following order. Each script generates data required by the next.

### 1. Biological Age Calculation
*   **Script**: `biological_age_calculator.py`
*   **Input**: Synthesized NHANES-like data (internal demo)
*   **Output**: `Biological_Age_Actuarial_Report.csv`
*   **Purpose**: Validates the core PhenoAge algorithm and generates the "Actuarial Report".

### 2. NHANES 2003-2006 Data Validation
*   **Script**: `nhanes_2003_2006_validation.py`
*   **Input**: Downloads NHANES 2003-2006 data from CDC
*   **Output**: `nhanes_2003_2006_phenoage_results.csv`
*   **Purpose**: Applies the algorithm to the historical cohort used for mortality linkage.

### 3. Mortality Validation (The Gold Standard)
*   **Script**: `mortality_validation.py`
*   **Input**: `nhanes_2003_2006_phenoage_results.csv` (from step 2) + NDI Mortality Files (auto-downloaded)
*   **Output**: `phenoage_with_mortality.csv`
*   **Purpose**: Links biological age to actual death records and calculates Hazard Ratios (HR = 1.081).

### 4. DeepSurv Validation
*   **Script**: `deepsurv_validation.py`
*   **Input**: `phenoage_with_mortality.csv` (from step 3)
*   **Output**: `deepsurv_validation_results.csv`
*   **Purpose**: Trains the Deep Learning model on the mortality data and confirms the C-Index (0.887).

---

## 📂 Key Files

| File | Description |
|---|---|
| `biological_age_calculator.py` | Core algorithm implementation (Levine et al. 2018). |
| `wearable_models.py` | Comparative analysis (DeepSurv vs XGBoost vs CoxPH). |
| `accelerometer_integration.py` | Processing pipeline for PAX (wearable) data. |
| `Final_Thesis_Manuscript.md` | The complete thesis text. |

## ⚠️ Notes
*   **Dependencies**: Scripts will attempt to auto-install missing packages (`lifelines`, `torch`, `xgboost`).
*   **Data**: Data files are saved to `./nhanes_2003_2006_data` and `./nhanes_data`.
