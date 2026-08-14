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
        
        graded_results.append({
            "filename": filename,
            "score": omr_score,
            "responses": cleaned_responses
        })
        
    return graded_results
