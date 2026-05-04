function loadChart(spamCount, safeCount) {

    const ctx = document.getElementById("chart");

    new Chart(ctx, {
        type: "pie",
        data: {
            labels: ["Spam", "Safe"],
            datasets: [{
                data: [spamCount, safeCount]
            }]
        }
    });

}
