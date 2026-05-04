function checkSpam() {
    const emailContent = document.getElementById('emailContent').value;
    
    // Selectors for the new UI elements
    const analyzeBtn = document.querySelector('.btn-analyze');
    const btnText = document.getElementById('btnText');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultBox = document.getElementById('resultBox');
    const resultContent = document.getElementById('resultContent');
    
    if(!emailContent.trim()) return alert("Please paste an email first!");

    // UI Loading State
    if(btnText) btnText.style.display = 'none';
    if(loadingSpinner) loadingSpinner.style.display = 'inline-block';
    analyzeBtn.disabled = true;

    // Use the absolute path to your Flask route
    fetch('/analyze', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: emailContent })
    })
    .then(res => {
        if (!res.ok) throw new Error("Server Error: " + res.status);
        return res.json();
    })
    .then(data => {
        const isSpam = data.result.toLowerCase().includes('spam');
        const themeColor = isSpam ? '#ef4444' : '#10b981'; 
        const statusText = isSpam ? 'SPAM DETECTED' : 'SAFE EMAIL';

        resultBox.style.display = 'block';
        resultContent.innerHTML = `
            <h2 style="color: ${themeColor}; text-transform: uppercase; margin-bottom: 10px;">
                ${statusText}
            </h2>
            
            <div style="font-size: 24px; font-weight: bold; color: #1e293b; margin-bottom: 15px;">
                Threat Score: <span style="color: ${themeColor};">${data.score}%</span>
            </div>
            
            <p><strong>AI Analysis:</strong> ${data.reason}</p>
        `;
        
        // Reset button
        analyzeBtn.disabled = false;
        btnText.style.display = 'inline';
        loadingSpinner.style.display = 'none';
    })
    .catch(err => {
        console.error(err);
        alert("Connection Failed. Check your Python Terminal for errors.");
        if(btnText) btnText.style.display = 'inline';
        if(loadingSpinner) loadingSpinner.style.display = 'none';
        analyzeBtn.disabled = false;
    });
}

function updateHistoryTable(data) {
    const tableBody = document.getElementById('historyTableBody');
    const newRow = document.createElement('tr');
    
    const isSpam = data.result.toLowerCase().includes('spam');
    const color = isSpam ? 'red' : 'green';

    newRow.innerHTML = `
        <td>${new Date().toLocaleDateString()}</td>
        <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis;">${data.preview}</td>
        <td style="color: ${color}; font-weight: bold;">${data.result}</td>
        <td style="color: ${color}; font-weight: bold;">${data.score}%</td>
    `;
    
    tableBody.prepend(newRow); // Adds the new result to the top
}