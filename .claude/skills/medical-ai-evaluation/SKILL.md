---
name: medical-ai-evaluation
description: Design and review leakage-safe, non-clinical medical AI or biomedical ML evaluation. Use when a repository handles medical images, clinical/tabular signals, diagnosis labels, sensitivity/specificity, ROC AUC, confusion matrices, operating thresholds, patient splits, dataset licensing, or safety limitations.
---

# Medical AI Evaluation

## Bound The Claim

1. State the exact prediction question, positive class, population represented by the dataset and intended non-clinical use.
2. Do not claim diagnosis, clinical safety, deployment readiness or demographic generalization without evidence designed for that claim.
3. Put limitations beside the public metric, not only in a distant disclaimer.

## Prove Dataset Provenance

1. Record canonical source, version, license, archive checksum, class mapping, split sizes and redistribution constraints.
2. Verify archive keys, shapes, dtypes and split counts before feature extraction.
3. Use official splits when available. Enforce patient-level isolation when patient identifiers exist; if identifiers are absent, state that patient-level leakage could not be independently verified.
4. Reject a synthetic benchmark when labels directly control the same features measured by the classifier. Such a score proves only the generator-classifier coupling.

## Prevent Leakage

1. Fit preprocessing and model parameters on training data only.
2. Select hyperparameters and operating thresholds on validation data only.
3. Keep the test split untouched until final evaluation. Test metrics must never influence fitting, threshold selection or model choice.
4. Encode these boundaries as functions/tests so leakage prevention is executable, not prose.

## Report Useful Metrics

1. Use discrimination metrics such as ROC AUC with operating-point metrics such as sensitivity and specificity.
2. Report TN, FP, FN and TP plus total and positive-class sample counts.
3. Include accuracy only with class balance context. Add PR AUC, confidence intervals or subgroup analysis when the data and claim justify them.
4. Version threshold policy, class ID, dataset split and comparability key with the result.

## Architecture And Runtime

1. Prefer a deterministic evaluation pipeline unless external actors create real substitution boundaries.
2. Keep dataset integrity, features, fitting, threshold selection and test evaluation as separate stages.
3. Use a transparent CPU baseline first when the repository proves methodology. Add deep learning only for a measured quality/cost question.
4. Run offline in pinned Docker and generate provenance-rich V2 evidence from a clean source commit and immutable image.

## Publication Gate

Require tests for checksum/split validation, threshold isolation, invalid inputs and confusion-matrix consistency. README, manifest, SDD, OpenSpec, dataset license, raw JSON and V2 evidence must agree before status becomes `published`.
