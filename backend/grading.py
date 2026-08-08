def grade_results(raw_omr_data, answer_key=None):
    """
    Adapted grading logic. 
    raw_omr_data is expected to be a list of rows from OMRChecker's CSV output.
    """
    graded_results = []
    
    for row in raw_omr_data:
        # The exact structure depends on the template columns.
        # Typically row[0] is image name, row[1] is file path, row[2] is saved path, row[3] is score
        # The rest are question responses.
        if len(row) < 5:
            continue
            
        filename = row[0]
        omr_score = row[3] 
        responses = row[4:]
        
        # For PencilTrace, if answer_key is provided, we might re-score it here.
        # Otherwise we trust OMRChecker's internal evaluation if configured.
        
        graded_results.append({
            "filename": filename,
            "score": omr_score,
            "responses": responses
        })
        
    return graded_results
