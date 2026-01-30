window.uploadedData=null;window.fittedResults=null;window.currentParams=null;$(document).ready(function(){$("#uploadForm").on("submit",handleUpload),$("#fitBtn").on("click",handleFit),$("#updateBtn").on("click",handleInteractiveUpdate)});function handleUpload(e){e.preventDefault();const t=new FormData(e.target),a=$("#uploadStatus");a.removeClass("success error").addClass("info").text("Uploading and processing data...").show(),$.ajax({url:"/api/upload",type:"POST",data:t,processData:!1,contentType:!1,success:function(e){if(e.success){window.uploadedData=e.data,a.removeClass("info").addClass("success").html(`✓ Data loaded successfully!<br>📊 ${e.data.num_points} data points processed<br>🔢 f1 = ${e.data.f1.toFixed(4)}`),showRawLines(e.data.raw_lines),showDataPreview(e.data.preview),$("#fittingSection").slideDown(),$("html, body").animate({scrollTop:$("#rawPreview").offset().top-20},500)}else a.removeClass("info").addClass("error").text("Error: "+e.error)},error:function(e){a.removeClass("info").addClass("error").text("✗ Error: "+(e.responseJSON?.error||"Upload failed"))}})}function showRawLines(e){const t=$("#rawLinesBody");t.empty();for(let a=0;a<e.length;a++)t.append(`<tr><td>${a+1}</td><td class="raw-line">${escapeHtml(e[a])}</td></tr>`);$("#rawPreview").slideDown()}function escapeHtml(e){return e.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;")}function showDataPreview(e){const t=$("#previewBody");t.empty();for(let a=0;a<5&&a<e.first_5_current.length;a++)t.append(`<tr><td>${e.first_5_current[a].toExponential(4)}</td><td>${e.first_5_potential[a].toFixed(4)}</td></tr>`);$("#dataPreview").slideDown()}function handleFit(){if(!window.uploadedData)return alert("Please upload data first!");const e=$("#fitStatus"),t=$("#fitBtn");e.removeClass("success error").addClass("info").text("Fitting data... This may take a moment.").show(),t.prop("disabled",!0).html('<span class="spinner"></span> Fitting...');const a={potential:window.uploadedData.potential,current:window.uploadedData.current,model_type:$("#modelType").val(),f1:window.uploadedData.f1,bbv_initial:parseFloat($("#bbvInitial").val()),bbh_initial:parseFloat($("#bbhInitial").val()),vary_bbv:$("#varyBbv").is(":checked"),vary_bbh:$("#varyBbh").is(":checked")};$.ajax({url:"/api/fit",type:"POST",contentType:"application/json",data:JSON.stringify(a),success:function(a){a.success?(window.fittedResults=a,window.currentParams=a.fitted_params,e.removeClass("info").addClass("success").text("✓ Fitting completed successfully!"),t.prop("disabled",!1).text("Fit Data"),displayResults(a),$("#resultsSection").slideDown(),$("html, body").animate({scrollTop:$("#resultsSection").offset().top-20},500)):(e.removeClass("info").addClass("error").text("Error: "+a.error),t.prop("disabled",!1).text("Fit Data"))},error:function(a){e.removeClass("info").addClass("error").html("✗ Error: "+(a.responseJSON?.error||"Fitting failed")+(a.responseJSON?.traceback?"<br><pre>"+a.responseJSON.traceback+"</pre>":"")),t.prop("disabled",!1).text("Fit Data")}})}function displayResults(e){const t=$("#paramsBody");t.empty();for(const[a,s]of Object.entries(e.fitted_params))t.append(`<tr><td>${a}</td><td>${s.toExponential(4)}</td></tr>`);$("#statsDisplay").html(`<p><strong>χ²:</strong> ${e.statistics.chi_squared.toExponential(4)}</p><p><strong>Reduced χ²:</strong> ${e.statistics.reduced_chi_squared.toExponential(4)}</p>${e.statistics.r_squared?`<p><strong>R²:</strong> ${e.statistics.r_squared.toFixed(6)}</p>`:""}`),createSliders(e.fitted_params),createPlots(e)}function createSliders(e){const t=$("#sliderControls");t.empty();for(const[a,s]of Object.entries(e)){const e=["k1","k1r","k2","k2r"].includes(a);let r,n,l,i;e?(r=(l=Math.log10(s))-3,n=l+3,l=.1,i=s.toExponential(3)):(r=0,n=1,l=.01,i=s.toFixed(4)),t.append(`<div class="slider-group"><label for="slider_${a}">${a}:</label><input type="range" id="slider_${a}" min="${r}" max="${n}" step="${l}" value="${e?Math.log10(s):s}" data-param="${a}" data-is-log="${e}"><span class="slider-value" id="value_${a}">${i}</span></div>`)}$('input[type="range"]').on("input",function(){const e=$(this).data("param"),t=$(this).data("is-log");let a=parseFloat($(this).val());t?(a=Math.pow(10,a),$(`#value_${e}`).text(a.toExponential(3))):$(`#value_${e}`).text(a.toFixed(4)),window.currentParams[e]=a})}function handleInteractiveUpdate(){if(!window.uploadedData||!window.currentParams)return alert("Please fit data first!");$.ajax({url:"/api/calculate",type:"POST",contentType:"application/json",data:JSON.stringify({potential:window.uploadedData.potential,f1:window.uploadedData.f1,...window.currentParams}),success:function(e){e.success&&updatePlots(e.predictions)},error:function(e){alert("Calculation failed: "+(e.responseJSON?.error||"Unknown error"))}})}function createPlots(e){const t=e.predictions;Plotly.newPlot("plot1",[{x:window.uploadedData.potential,y:window.uploadedData.current.map(e=>1e3*e),mode:"markers",name:"Experimental",marker:{size:4,color:"blue"}},{x:t.potential,y:t.current.map(e=>1e3*e),mode:"lines",name:"Fitted",line:{color:"red",width:2}}],{title:"Current vs Potential",xaxis:{title:"Potential vs RHE (V)"},yaxis:{title:"Current Density (mA/cm²)"},hovermode:"closest"},{responsive:!0}),Plotly.newPlot("plot2",[{x:t.potential,y:t.theta,mode:"lines",name:"θ (H-ads)",line:{color:"green",width:2}},{x:t.potential,y:t.theta_inv,mode:"lines",name:"1-θ (empty)",line:{color:"orange",width:2,dash:"dash"}}],{title:"Surface Coverage",xaxis:{title:"Potential vs RHE (V)"},yaxis:{title:"Coverage"},hovermode:"closest"},{responsive:!0}),Plotly.newPlot("plot3",[{x:t.tafel_exp_pot,y:t.tafel_exp_slope,mode:"markers",name:"Experimental",marker:{size:6,color:"blue",symbol:"square"}},{x:t.tafel_theo_pot,y:t.tafel_theo_slope,mode:"lines+markers",name:"Theoretical",line:{color:"red",width:2},marker:{size:4}}],{title:"Tafel Slope Analysis",xaxis:{title:"Mean Potential vs RHE (V)"},yaxis:{title:"Tafel Slope (mV/dec)"},hovermode:"closest"},{responsive:!0})}function updatePlots(e){Plotly.restyle("plot1",{y:[e.current.map(e=>1e3*e)]},[1]),Plotly.restyle("plot2",{y:[e.theta,e.theta_inv]},[0,1]),Plotly.restyle("plot3",{x:[e.tafel_theo_pot],y:[e.tafel_theo_slope]},[1])}


// Export functionality with debugging
$(document).ready(function() {
    $('#exportBtn').click(function() {
        console.log('Export button clicked');
        console.log('window.fittedResults:', window.fittedResults);
        console.log('window.uploadedData:', window.uploadedData);
        
        if (!window.fittedResults) {
            alert('No fitting results available to export');
            return;
        }
        
        const exportData = {
            fitted_params: window.fittedResults.fitted_params,
            statistics: window.fittedResults.statistics,
            potential: window.uploadedData.potential,
            current: window.uploadedData.current,
            theoretical_current: window.fittedResults.predictions.current,
            theta: window.fittedResults.predictions.theta,
            theta_inv: window.fittedResults.predictions.theta_inv,
            tafel_pot: window.fittedResults.predictions.tafel_exp_pot,
            tafel_slopes: window.fittedResults.predictions.tafel_exp_slope,
            tafel_theo_pot: window.fittedResults.predictions.tafel_theo_pot,
            tafel_theo_slopes: window.fittedResults.predictions.tafel_theo_slope,
            model_type: $("#modelType").val()
        };
        
        console.log('Export data prepared:', exportData);
        
        $.ajax({
            url: '/api/export',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(exportData),
            xhrFields: {
                responseType: 'blob'
            },
            success: function(blob) {
                console.log('Export successful, blob size:', blob.size);
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'HER_Analysis_Results_' + new Date().toISOString().split('T')[0] + '.zip';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            },
            error: function(xhr) {
                console.error('Export error:', xhr);
                alert('Export failed: ' + (xhr.responseText || 'Unknown error'));
            }
        });
    });
});
