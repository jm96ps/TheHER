@app.route('/api/upload', methods=['POST'])
def upload_data():
    """
    Handle data file upload and initial processing
    Returns: JSON with processed data and initial parameters
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get parameters from form
        area_electrode = float(request.form.get('area_electrode', 0.5))
        ohmic_drop = float(request.form.get('ohmic_drop', 6.43))
        ref_correction = float(request.form.get('ref_correction', 0.924))
        temperature = float(request.form.get('temperature', 298.15))
        gas_constant = float(request.form.get('gas_constant', 8.314))
        current_column = int(request.form.get('current_column', 0))
        potential_column = int(request.form.get('potential_column', 1))
        skip_rows = int(request.form.get('skip_rows', 1))
        
        # Calculate f1
        f1 = F / (temperature * gas_constant)
        
        # Read uploaded file
        # Save temporarily
        temp_path = '/tmp/temp_data.txt'
        file.save(temp_path)
        
        # Read first 10 lines for preview
        with open(temp_path, 'r') as f:
            first_10_lines = [f.readline().rstrip() for _ in range(10)]
        
        # Load data with flexible separator detection
        # Try to detect separator and read with pandas
        df = pd.read_csv(temp_path, sep=None, engine='python', skiprows=skip_rows, header=None)
        
        # Extract columns based on user selection
        current_raw = df.iloc[:, current_column].values
        potential_raw = df.iloc[:, potential_column].values
        
        # Process
        current = current_raw / area_electrode
        potential = potential_raw - (current_raw * ohmic_drop) + ref_correction
        
        # Clean up temp file
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'data': {
                'potential': potential.tolist(),
                'current': current.tolist(),
                'f1': f1,
                'num_points': len(potential),
                'preview': {
                    'first_5_current': current[:5].tolist(),
                    'first_5_potential': potential[:5].tolist()
                },
                'raw_lines': first_10_lines
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
