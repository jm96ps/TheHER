// HER Analysis Platform - JavaScript

let uploadedData = null;
let fittedResults = null;
let currentParams = null;

// Initialize when DOM is ready
$(document).ready(function() {
    console.log('HER Analysis Platform loaded');
    
    // Handle file upload
    $('#uploadForm').on('submit', handleUpload);
    
    // Handle fitting
    $('#fitBtn').on('click', handleFit);
    
    // Handle interactive update
    $('#updateBtn').on('click', handleInteractiveUpdate);
});

// Handle data upload
function handleUpload(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const statusDiv = $('#uploadStatus');
    
    statusDiv.removeClass('success error').addClass('info').text('Uploading and processing data...').show();
    
    $.ajax({
        url: '/api/upload',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            if (response.success) {
                uploadedData = response.data;
                statusDiv.removeClass('info').addClass('success')
                    .html(`✓ Data loaded successfully! ${response.data.num_points} data points processed. f1 = ${response.data.f1.toFixed(4)}`);
                
                // Show fitting section
                $('#fittingSection').slideDown();
                
                // Scroll to fitting section
                $('html, body').animate({
                    scrollTop: $('#fittingSection').offset().top - 20
                }, 500);
            } else {
                statusDiv.removeClass('info').addClass('error').text('Error: ' + response.error);
            }
        },
        error: function(xhr) {
            const errorMsg = xhr.responseJSON?.error || 'Upload failed';
            statusDiv.removeClass('info').addClass('error').text('✗ Error: ' + errorMsg);
        }
    });
}

// Handle fitting
function handleFit() {
    if (!uploadedData) {
        alert('Please upload data first!');
        return;
    }
    
    const statusDiv = $('#fitStatus');
    const fitBtn = $('#fitBtn');
    
    statusDiv.removeClass('success error').addClass('info').text('Fitting data... This may take a moment.').show();
    fitBtn.prop('disabled', true).html('<span class="spinner"></span> Fitting...');
    
    const fitData = {
        potential: uploadedData.potential,
        current: uploadedData.current,
        model_type: $('#modelType').val(),
        f1: uploadedData.f1,
        bbv_initial: parseFloat($('#bbvInitial').val()),
        bbh_initial: parseFloat($('#bbhInitial').val()),
        vary_bbv: $('#varyBbv').is(':checked'),
        vary_bbh: $('#varyBbh').is(':checked')
    };
    
    $.ajax({
        url: '/api/fit',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(fitData),
        success: function(response) {
            if (response.success) {
                fittedResults = response;
                currentParams = response.fitted_params;
                
                statusDiv.removeClass('info').addClass('success').text('✓ Fitting completed successfully!');
                fitBtn.prop('disabled', false).text('Fit Data');
                
                // Display results
                displayResults(response);
                
                // Show results section
                $('#resultsSection').slideDown();
                
                // Scroll to results
                $('html, body').animate({
                    scrollTop: $('#resultsSection').offset().top - 20
                }, 500);
            } else {
                statusDiv.removeClass('info').addClass('error').text('Error: ' + response.error);
                fitBtn.prop('disabled', false).text('Fit Data');
            }
        },
        error: function(xhr) {
            const errorMsg = xhr.responseJSON?.error || 'Fitting failed';
            statusDiv.removeClass('info').addClass('error').html('✗ Error: ' + errorMsg + 
                (xhr.responseJSON?.traceback ? '<br><pre>' + xhr.responseJSON.traceback + '</pre>' : ''));
            fitBtn.prop('disabled', false).text('Fit Data');
        }
    });
}

// Display results
function displayResults(results) {
    // Display fitted parameters
    const paramsBody = $('#paramsBody');
    paramsBody.empty();
    
    for (const [param, value] of Object.entries(results.fitted_params)) {
        paramsBody.append(`
            <tr>
                <td>${param}</td>
                <td>${value.toExponential(4)}</td>
            </tr>
        `);
    }
    
    // Display statistics
    const statsDiv = $('#statsDisplay');
    statsDiv.html(`
        <p><strong>χ²:</strong> ${results.statistics.chi_squared.toExponential(4)}</p>
        <p><strong>Reduced χ²:</strong> ${results.statistics.reduced_chi_squared.toExponential(4)}</p>
        ${results.statistics.r_squared ? `<p><strong>R²:</strong> ${results.statistics.r_squared.toFixed(6)}</p>` : ''}
    `);
    
    // Create interactive sliders
    createSliders(results.fitted_params);
    
    // Create plots
    createPlots(results);
}

// Create interactive sliders
function createSliders(params) {
    const slidersDiv = $('#sliderControls');
    slidersDiv.empty();
    
    for (const [param, value] of Object.entries(params)) {
        const isLog = ['k1', 'k1r', 'k2', 'k2r'].includes(param);
        
        let min, max, step, displayValue;
        
        if (isLog) {
            // Logarithmic scale for rate constants
            const logValue = Math.log10(value);
            min = logValue - 3;
            max = logValue + 3;
            step = 0.1;
            displayValue = value.toExponential(3);
        } else {
            // Linear scale for symmetry factors
            min = 0;
            max = 1;
            step = 0.01;
            displayValue = value.toFixed(4);
        }
        
        slidersDiv.append(`
            <div class="slider-group">
                <label for="slider_${param}">${param}:</label>
                <input type="range" id="slider_${param}" 
                       min="${min}" max="${max}" step="${step}" 
                       value="${isLog ? Math.log10(value) : value}"
                       data-param="${param}" data-is-log="${isLog}">
                <span class="slider-value" id="value_${param}">${displayValue}</span>
            </div>
        `);
    }
    
    // Add event listeners to sliders
    $('input[type="range"]').on('input', function() {
        const param = $(this).data('param');
        const isLog = $(this).data('is-log');
        let value = parseFloat($(this).val());
        
        if (isLog) {
            value = Math.pow(10, value);
            $(`#value_${param}`).text(value.toExponential(3));
        } else {
            $(`#value_${param}`).text(value.toFixed(4));
        }
        
        currentParams[param] = value;
    });
}

// Handle interactive update
function handleInteractiveUpdate() {
    if (!uploadedData || !currentParams) {
        alert('Please fit data first!');
        return;
    }
    
    const calcData = {
        potential: uploadedData.potential,
        f1: uploadedData.f1,
        ...currentParams
    };
    
    $.ajax({
        url: '/api/calculate',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(calcData),
        success: function(response) {
            if (response.success) {
                // Update plots with new predictions
                updatePlots(response.predictions);
            }
        },
        error: function(xhr) {
            alert('Calculation failed: ' + (xhr.responseJSON?.error || 'Unknown error'));
        }
    });
}

// Create plots
function createPlots(results) {
    const predictions = results.predictions;
    
    // Plot 1: Current vs Potential
    const trace1_exp = {
        x: uploadedData.potential,
        y: uploadedData.current.map(c => c * 1000),
        mode: 'markers',
        name: 'Experimental',
        marker: { size: 4, color: 'blue' }
    };
    
    const trace1_fit = {
        x: predictions.potential,
        y: predictions.current.map(c => c * 1000),
        mode: 'lines',
        name: 'Fitted',
        line: { color: 'red', width: 2 }
    };
    
    const layout1 = {
        title: 'Current vs Potential',
        xaxis: { title: 'Potential vs RHE (V)' },
        yaxis: { title: 'Current Density (mA/cm²)' },
        hovermode: 'closest'
    };
    
    Plotly.newPlot('plot1', [trace1_exp, trace1_fit], layout1, {responsive: true});
    
    // Plot 2: Surface Coverage
    const trace2_theta = {
        x: predictions.potential,
        y: predictions.theta,
        mode: 'lines',
        name: 'θ (H-ads)',
        line: { color: 'green', width: 2 }
    };
    
    const trace2_theta_inv = {
        x: predictions.potential,
        y: predictions.theta_inv,
        mode: 'lines',
        name: '1-θ (empty)',
        line: { color: 'orange', width: 2, dash: 'dash' }
    };
    
    const layout2 = {
        title: 'Surface Coverage',
        xaxis: { title: 'Potential vs RHE (V)' },
        yaxis: { title: 'Coverage' },
        hovermode: 'closest'
    };
    
    Plotly.newPlot('plot2', [trace2_theta, trace2_theta_inv], layout2, {responsive: true});
    
    // Plot 3: Tafel Slopes
    const trace3_exp = {
        x: predictions.tafel_exp_pot,
        y: predictions.tafel_exp_slope,
        mode: 'markers',
        name: 'Experimental',
        marker: { size: 6, color: 'blue', symbol: 'square' }
    };
    
    const trace3_theo = {
        x: predictions.tafel_theo_pot,
        y: predictions.tafel_theo_slope,
        mode: 'lines+markers',
        name: 'Theoretical',
        line: { color: 'red', width: 2 },
        marker: { size: 4 }
    };
    
    const layout3 = {
        title: 'Tafel Slope Analysis',
        xaxis: { title: 'Mean Potential vs RHE (V)' },
        yaxis: { title: 'Tafel Slope (mV/dec)' },
        hovermode: 'closest'
    };
    
    Plotly.newPlot('plot3', [trace3_exp, trace3_theo], layout3, {responsive: true});
}

// Update plots with new predictions
function updatePlots(predictions) {
    // Update Plot 1 - fitted curve only
    Plotly.restyle('plot1', {
        y: [predictions.current.map(c => c * 1000)]
    }, [1]);
    
    // Update Plot 2 - surface coverage
    Plotly.restyle('plot2', {
        y: [predictions.theta, predictions.theta_inv]
    }, [0, 1]);
    
    // Update Plot 3 - Tafel slopes (theoretical only)
    Plotly.restyle('plot3', {
        x: [predictions.tafel_theo_pot],
        y: [predictions.tafel_theo_slope]
    }, [1]);
}
