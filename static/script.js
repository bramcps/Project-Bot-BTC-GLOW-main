// --- STATE MANAGEMENT (MEMORI FRONTEND) ---
let inPosition = false;
let buyPrice = 0.0;
let chart;

// --- ELEMEN DOM ---
const currentPriceEl = document.getElementById('current-price');
const high24hEl = document.getElementById('high-24h');
const low24hEl = document.getElementById('low-24h');
const predictionPriceEl = document.getElementById('prediction-price');
const statusBoxEl = document.getElementById('status-box');
const statusTextEl = document.getElementById('status-text');
const pnlValueEl = document.getElementById('pnl-value');
const logBoxEl = document.getElementById('log-box');
const aiSignalEl = document.getElementById('ai-signal');
const botDecisionEl = document.getElementById('bot-decision');

// --- PENGATURAN GRAFIK APEXCHARTS ---
const chartOptions = {
    series: [{
        data: []
    }],
    chart: {
        type: 'candlestick',
        height: '100%',
        foreColor: '#d1d4dc',
        background: 'transparent'
    },
    title: {
        text: 'BTC/USD - 5 Menit',
        align: 'left',
        style: {
            color: '#d1d4dc'
        }
    },
    xaxis: {
        type: 'datetime'
    },
    yaxis: {
        tooltip: {
            enabled: true
        },
        labels: {
            formatter: function (val) {
                return val.toFixed(2);
            }
        }
    },
    tooltip: {
        theme: 'dark'
    },
    grid: {
        borderColor: '#2a2e39'
    }
};

// Inisialisasi grafik saat halaman dimuat
document.addEventListener('DOMContentLoaded', () => {
    chart = new ApexCharts(document.querySelector("#candlestick-chart"), chartOptions);
    chart.render();
    fetchData(); // Panggil data pertama kali
});

// --- FUNGSI UTAMA UNTUK MENGAMBIL DATA & MENG-UPDATE UI ---
async function fetchData() {
    try {
        const response = await fetch('/api/live_data');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        // 1. Update Header Metrics
        const currentPrice = data.current_price;
        currentPriceEl.textContent = `$${currentPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        high24hEl.textContent = `$${data.high_24h.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        low24hEl.textContent = `$${data.low_24h.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        predictionPriceEl.textContent = `$${data.prediction.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

        // 2. Update Grafik Candlestick
        const chartData = data.chart_data.map(d => ({
            x: new Date(d.Date),
            y: [d.Open, d.High, d.Low, d.Close]
        }));
        chart.updateSeries([{ data: chartData }]);

        // 3. Logika Rekomendasi & Trading
        const targetProfitPercent = parseFloat(document.getElementById('target-profit').value);
        const stopLossPercent = parseFloat(document.getElementById('stop-loss').value);

        let aiSignal = "TAHAN";
        if (data.prediction > currentPrice * 1.001) {
            aiSignal = "BELI";
        } else if (data.prediction < currentPrice * 0.999) {
            aiSignal = "JUAL";
        }
        aiSignalEl.textContent = aiSignal;

        let botDecision = "Menunggu...";
        if (!inPosition) {
            if (aiSignal === "BELI") {
                inPosition = true;
                buyPrice = currentPrice;
                botDecision = `MEMBELI @ ${currentPrice.toFixed(2)}`;
                addLog(botDecision, 'buy');
            }
        } else {
            const pnl = ((currentPrice - buyPrice) / buyPrice) * 100;
            const targetPrice = buyPrice * (1 + targetProfitPercent / 100);
            const stopLossPrice = buyPrice * (1 - stopLossPercent / 100);

            if (currentPrice >= targetPrice) {
                botDecision = `SELL ON PROFIT @ ${currentPrice.toFixed(2)}`;
                addLog(`${botDecision} (P/L: +${pnl.toFixed(2)}%)`, 'profit');
                inPosition = false;
            } else if (currentPrice <= stopLossPrice) {
                botDecision = `STOP LOSS @ ${currentPrice.toFixed(2)}`;
                addLog(`${botDecision} (P/L: ${pnl.toFixed(2)}%)`, 'loss');
                inPosition = false;
            } else {
                botDecision = `MENAHAN POSISI...`;
            }
            pnlValueEl.textContent = `${pnl.toFixed(2)}%`;
        }
        botDecisionEl.textContent = botDecision;
        updateStatusUI();

    } catch (error) {
        console.error("Gagal mengambil data:", error);
        addLog(`Error: ${error.message}`, 'error');
    }
}

// --- FUNGSI BANTUAN ---
function addLog(message, type) {
    const logEntry = document.createElement('p');
    const timestamp = new Date().toLocaleTimeString();
    logEntry.textContent = `[${timestamp}] ${message}`;
    logEntry.className = type; // Untuk pewarnaan di masa depan
    logBoxEl.prepend(logEntry);
}

function updateStatusUI() {
    if (inPosition) {
        statusBoxEl.className = 'status-box status-active';
        statusTextEl.textContent = 'POSISI AKTIF';
    } else {
        statusBoxEl.className = 'status-box status-inactive';
        statusTextEl.textContent = 'TIDAK AKTIF';
        pnlValueEl.textContent = 'N/A';
    }
}

// --- LOOP UTAMA ---
// Memanggil fetchData setiap 30 detik
setInterval(fetchData, 30000);
