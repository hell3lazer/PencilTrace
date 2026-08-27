def grade_results(raw_omr_data, answer_key=None):
    """
    Adapted grading logic. 
    raw_omr_data is expected to be a list of rows from OMRChecker's CSV output.
    """
    graded_results = []
    
    for row in raw_omr_data:
        if len(row) < 5 or row[0] == 'file_id':
            continue
            
        filename = row[0]
        omr_score = row[3] 
        responses = row[4:]
        
        # Clean up missing/multiple answers
        cleaned_responses = [str(r) if str(r) != "MULTI" else "" for r in responses]
        
        if answer_key and len(cleaned_responses) > 1:
            correct = 0
            total = min(len(answer_key), len(cleaned_responses) - 1)
            for i in range(total):
                if cleaned_responses[i+1].strip().upper() == str(answer_key[i]).strip().upper():
                    correct += 1
            omr_score = f"{correct}/{total}"
        
        graded_results.append({
            "filename": filename,
            "score": omr_score,
            "responses": cleaned_responses
        })
        
    return graded_results
