def get_summary_sentences(missing_count, duplicate_count, quality_score):
    summary_sentences = []
    summary_sentences.append("Dataset validation completed successfully.")
    
    if missing_count == 0:
        summary_sentences.append("No missing values detected.")
    else:
        summary_sentences.append(f"Detected {missing_count} missing values.")
        
    if duplicate_count == 0:
        summary_sentences.append("No duplicate records detected.")
    else:
        summary_sentences.append(f"Detected {duplicate_count} duplicate records.")
        
    if missing_count == 0 and duplicate_count == 0:
        summary_sentences.append("Dataset schema is consistent.")
        summary_sentences.append("Data quality score is excellent.")
        summary_sentences.append("Dataset is ready for analytics, dashboarding, forecasting and machine learning.")
    else:
        summary_sentences.append("Dataset schema is consistent.")
        if quality_score >= 95:
            summary_sentences.append(f"Data quality score is very high ({quality_score}%).")
        else:
            summary_sentences.append(f"Data quality score is {quality_score}%.")
        summary_sentences.append("Dataset is ready for analytics and dashboarding.")
    return summary_sentences

# Test case 1: No missing values / No duplicates
res1 = get_summary_sentences(0, 0, 100.0)
print("Test Case 1 (0 missing, 0 duplicate, 100.0%):")
for s in res1:
    print(f"- {s}")
assert res1 == [
    "Dataset validation completed successfully.",
    "No missing values detected.",
    "No duplicate records detected.",
    "Dataset schema is consistent.",
    "Data quality score is excellent.",
    "Dataset is ready for analytics, dashboarding, forecasting and machine learning."
]

# Test case 2: Missing values only
res2 = get_summary_sentences(5, 0, 98.2)
print("\nTest Case 2 (5 missing, 0 duplicate, 98.2%):")
for s in res2:
    print(f"- {s}")
assert res2 == [
    "Dataset validation completed successfully.",
    "Detected 5 missing values.",
    "No duplicate records detected.",
    "Dataset schema is consistent.",
    "Data quality score is very high (98.2%).",
    "Dataset is ready for analytics and dashboarding."
]

# Test case 3: Duplicates only
res3 = get_summary_sentences(0, 12, 96.5)
print("\nTest Case 3 (0 missing, 12 duplicate, 96.5%):")
for s in res3:
    print(f"- {s}")
assert res3 == [
    "Dataset validation completed successfully.",
    "No missing values detected.",
    "Detected 12 duplicate records.",
    "Dataset schema is consistent.",
    "Data quality score is very high (96.5%).",
    "Dataset is ready for analytics and dashboarding."
]

# Test case 4: Both missing and duplicates
res4 = get_summary_sentences(14, 5, 87.4)
print("\nTest Case 4 (14 missing, 5 duplicate, 87.4%):")
for s in res4:
    print(f"- {s}")
assert res4 == [
    "Dataset validation completed successfully.",
    "Detected 14 missing values.",
    "Detected 5 duplicate records.",
    "Dataset schema is consistent.",
    "Data quality score is 87.4%.",
    "Dataset is ready for analytics and dashboarding."
]

print("\nVerification Passed Successfully!")
